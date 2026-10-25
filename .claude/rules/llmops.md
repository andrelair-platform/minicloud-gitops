# LLMOps Standard — every custom AI product gets the full observability + prompt template

**The constraint (always-on):** any custom-built product that calls an LLM (RAG, agent, assistant,
extraction…) **MUST** wire the per-product LLMOps template — don't rebuild it ad-hoc. Two layers, **one
dedicated Langfuse project per product**:
- **Gateway layer (automatic):** LLM calls route through **LiteLLM** → auto-traced to the global
  `ai-gateway` project + per-call cost/tokens. Nothing to build.
- **App layer (mandatory to build):** the product's backend emits its own trace tree + managed prompts to
  a **dedicated Langfuse project**. The five mandatory pieces: **(1)** dedicated project + ESO-delivered
  keys + two-sided NetworkPolicy · **(2)** nested `Trace→Span→Generation` tree with model+token usage ·
  **(3)** `sessionId`+`userId` tags, dev+prod share ONE project via the `environment` attribute (never a
  2nd project per env) · **(4)** multi-modal inputs logged as generation input (when non-text) · **(5)**
  **prompt management** — prompts in Langfuse (Git = seed + runtime fallback), label-routed
  (prod=`production`, dev=`latest`), trace-linked for version attribution.

Reference implementation: **retrieva** (all five live on dev+prod).

> **HOW to wire it → the `wire-llmops` skill** (the step-by-step per section, the retrieva reference
> wiring, and the gotchas — ESO-SSA no-op, LiteLLM grant-by-model-NAME, ClickHouse-syslog-fills-PVC).
> Pulled on demand when building an LLM feature. Companions: `docs/ai-ml/per-product-llmops`,
> memories `[[reference_per_product_llmops]]`, `[[reference_retrieva_multimodal_ingestion]]`,
> `[[feedback_langfuse_clickhouse_syslog_pvc_full]]`.

Prod prompt/model promotion goes through the normal gate (Kargo/CODEOWNERS), never a manual hot-edit of prod.
