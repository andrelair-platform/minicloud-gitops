# RAG shared-service contract — multi-tenant ingest/retrieval + PII-gate-at-ingest

**Status:** Proposed · **Date:** 2026-11-22 · **Board:** AI Platform (#4)
**Scope:** operationalises the INGEST → INDEX → GOVERN stages of the Document Intelligence Spine for
*any* product that needs RAG.

> **This is NOT a new strategic decision — it is the operational contract under one.** The strategy is
> already Accepted in [`document-intelligence-spine.md`](./document-intelligence-spine.md): *build document
> intelligence once as a shared horizontal spine; business domains MUST NOT re-implement RAG privately.*
> This doc defines the **how**: the concrete multi-tenant API + per-product contract a product consumes,
> and the **PII-gate-at-ingest** the spine's GOVERN stage requires but that is **not yet wired in**.

## The problem it closes

"How do I avoid rebuilding the RAG pipeline for every product?" The spine ADR says *don't* — reuse the live
primitives (`markitdown-proxy` + Docling convert · `rag-ingest` chunk/embed · LiteLLM embeddings · Qdrant
vector store · Presidio PII). But today a product **can't cleanly consume** them because:

1. **No retrieval API.** `rag-ingest` exposes only `/ingest`. The agents (`minicloud-agent`,
   `crew-agent`) already call `RAG_INGEST_URL/query` — **which does not exist** → retrieval is each
   consumer's problem, inviting per-product re-implementation (the exact anti-pattern the spine forbids).
2. **No multi-tenant contract.** Collections exist (one per Open WebUI knowledge base UUID) but there is
   no agreed *"one product = one collection + its metadata/access policy"* convention — so "reuse" is
   ad-hoc.
3. **Governance is not inherited.** The spine mandates PII governance in the pipeline, but **Presidio is
   wired only into the LiteLLM *query* path, not ingest** — so documents are chunked, embedded and stored
   in Qdrant **with PII in plaintext in the payload**. A product consuming the shared pipeline does **not**
   automatically get PII protection. (See the investigation below.)

The fix for all three is the same: make the shared pipeline a **governed multi-tenant service with a
stable contract**, so a product consumes it by providing *data + config*, never code.

## Canonical facts (verified 2026-11-22)

- **Vector store = Qdrant** (`qdrant.ai.svc:6333`, v1.11.0). Open WebUI (`VECTOR_DB=qdrant`) is the anchor
  consumer; the deployed `rag-ingest` image writes there. ⚠️ The `minicloud-rag-ingest` repo `main.py` +
  README still describe the **rolled-back pgvector** variant (crashlooped on `PG_HOST` because Open WebUI
  reads Qdrant) — **stale docs; Qdrant is canonical.** (Fix that repo's docs separately.)
- **Embeddings:** LiteLLM alias `embeddings` → `mistral-embed` (EU, 1024-dim, cosine).
- **Qdrant payload** already stores `{text, document_type, section, source, article}` per point → **payload
  filtering for classification/access is feasible** (Qdrant supports it natively).
- **Presidio** (`analyzer` + `anonymizer`, `ai` ns, :3000) is **deployed and production-used** — but as a
  LiteLLM `pre_call` guardrail on *queries* only; **not** on ingest.
- **Convert step:** `markitdown-proxy` (`POST /v1/convert/file`) → images to Docling, everything else via
  MarkItDown → returns `{document:{md_content}}`.

## The contract — "one product = one collection"

A product gets RAG by **registering a collection and providing documents + config**. It provides no
pipeline code.

### Per-product collection manifest (the thin contract)
```yaml
collection: ktayl-claims-kb          # the tenant id (one per product/use-case)
owner: ktayl-claims                  # product / team that owns the corpus
classification: personal-data        # internal | personal-data | confidential (drives PII + access)
pii: true                            # run the PII gate at ingest (default: true)
access:                              # who may retrieve (deferred enforcement — see Right-sizing)
  roles: [claims-adjuster, claims-admin]
embedding: embeddings                # the LiteLLM alias (default: the platform standard)
```

### The two shared endpoints (the service contract)

| Endpoint | Who calls it | What it does |
|---|---|---|
| `POST /ingest` *(exists)* | any product / CronJob / Backstage action | `file + collection + source + doc_type` → convert → **PII-gate** → chunk → embed → upsert to Qdrant collection |
| `POST /query` *(**to build** — the gap)* | any product / agent / assistant | `{query, collection, top_k, filter?}` → embed question → Qdrant search **scoped to that collection** (+ access filter) → return chunks + **provenance** (source doc, section) |

`/query` is the missing half that makes retrieval a *platform* concern instead of each product's. It also
unbreaks the agents that already call it.

## Governance control #1 — PII-gate-at-ingest (grounded build)

The spine's GOVERN stage, made real at the one place text is plaintext before it becomes a vector.

**Where it slots in** (`minicloud-rag-ingest`, the *Qdrant* code path — NOT the stale pgvector `main.py`):
the chunking step, where each chunk's text exists plainly **before** `embed_batch`. Conceptually, in
`_make_chunk(text, …)` / the `chunk_by_structure` loop, **before** the chunk dict is embedded/stored:

```
for each chunk text:
    if collection.pii:                       # from the manifest (default true)
        analysis  = POST presidio-analyzer:3000/analyze     {text, language, entities}
        redacted  = POST presidio-anonymizer:3000/anonymize {text, analyzer_results}
        chunk.text      = redacted.text      # embed + store the REDACTED text
        chunk.metadata += {pii_detected: bool, pii_entities: [...]}   # audit trail
    # → embed(chunk.text) → upsert(collection, payload={text, **metadata})
```

Why here: metadata (doc_type/section/source) is preserved; only the served text is redacted; redacted text
is what gets embedded **and** what sits in the Qdrant payload. Reuses the **already-deployed** Presidio
(only a NetworkPolicy allowing `rag-ingest → presidio` is new — Presidio ingress is currently
`litellm`-only). No new service.

## Right-sizing (need-first — which parts now vs. deferred)

| Piece | Cost | Verdict |
|---|---|---|
| **PII-gate-at-ingest** (control #1) | medium (wire Presidio into ingest + 1 netpol) | **NOW** — the real compliance exposure (PII in plaintext vectors) |
| **Catalogue the collections** (register each as a governed dataset: owner/classification/retention) | low | **NOW** — closes "nobody knows what's in the vector store" |
| **`/query` endpoint** (shared retrieval + provenance) | medium | **NOW/SOON** — unbreaks agents; makes retrieval a platform concern |
| **Ingest freshness/failure alert** | low | **SOON** — mirror the data-platform CronJob-staleness pattern |
| **Entitlement-filtered retrieval** (enforce `access.roles` by filtering Qdrant payload per the caller's identity) | high (identity → per-chunk tags → filtered queries) | **DEFER** — trigger: real employees + sensitive corpora at volume |
| **Per-product isolated instance** (own pipeline via a Backstage scaffolder, config-not-code) | high | **DEFER** — only for a corpus with hard residency/scale needs; the shared multi-tenant service is the default |

## Consequences

- **Positive:** a product adopts RAG in ~a day (register a collection + POST its docs), not by forking a
  pipeline; governance (PII, classification, provenance) is built **once** in the shared service and
  **every** product inherits it; directly realises the spine ADR's "build once, many consumers."
- **Accepted trade-offs:** the shared service becomes a critical dependency needing clear API/SLA
  ownership (AI Platform #4); entitlement-filtered retrieval is deferred, so until then **retrieval is
  collection-scoped but not per-user role-filtered** — acceptable while the user base is small, a
  documented gap (not a silent one). Escalate when the trigger fires.

## Related

- Parent decision: [`document-intelligence-spine.md`](./document-intelligence-spine.md) (INGEST→…→GOVERN).
- Companion: AI as Governed Domain Copilots (ASSIST stage). · `platform-vs-information-system.md`
  (RAG = a platform capability the IS consumes). · Capability register (CAP-130/132/248 RAG/vector,
  CAP-317 PII masking). · Service repo: `minicloud-rag-ingest` (⚠️ docs describe the stale pgvector path).
