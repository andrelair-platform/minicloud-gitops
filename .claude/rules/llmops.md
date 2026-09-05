# LLMOps Standard — every custom AI product gets the full observability + prompt template

Any custom-built product that calls an LLM (RAG, agent, assistant, extraction…) must
wire the **per-product LLMOps template** below. This is the golden path — don't
rebuild it ad-hoc per project. Reference implementation: **retrieva** (all sections
live on dev + prod). Companion: `docs/ai-ml/per-product-llmops` (org docs),
memory `[[reference_per_product_llmops]]`, `[[reference_retrieva_multimodal_ingestion]]`.

Two layers, one dedicated Langfuse project per product:
- **Gateway layer (automatic):** LLM calls route through **LiteLLM** → auto-traced to
  the global `ai-gateway` project + per-call cost/tokens. Nothing to build.
- **App layer (this template):** the product's backend emits its own trace tree +
  managed prompts to a **dedicated Langfuse project**, authed with that product's keys.

## The mandatory checklist (per AI product)

### 1. Dedicated Langfuse project + governed wiring
- [ ] Create the project in the Langfuse UI (provisioning API is EE-gated on OSS).
- [ ] Keys → Vault `secret/platform/langfuse/<product>` → ESO → backend env
      (`LANGFUSE_BASE_URL` = in-cluster svc, `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY`).
- [ ] **Two-sided NetworkPolicy** (egress product→langfuse:3000 **and** langfuse
      `allow-app-tracing` ingress). Media (see §4) also needs egress to the blob store.

### 2. Nested trace hierarchy (full request lifecycle)
- [ ] `Trace` (one per request) → `Span`s (business steps) → `Generation`s (LLM calls)
      → retrieval/DB steps as **child spans** (not a flat sibling list). Use the core
      SDK manual spans (`langfuse-langchain` is incompatible with LangChain v1).
- [ ] Each `Generation` carries `model` + **token usage** (exact if the SDK returns it;
      an explicit estimate flagged `usageEstimated` otherwise — exact cost still lives
      in the gateway project).
- [ ] Null-safe, self-nesting trace handle so disabled-mode is a no-op (see retrieva
      `config/tracing.js`).

### 3. Session & user journey
- [ ] Every trace tagged with **`sessionId`** (the conversation/thread) + **`userId`**
      → enables retention, multi-turn degradation, and per-user consumption analysis.
- [ ] **Env, not a second project:** dev + prod share ONE project, distinguished by the
      native **`environment`** attribute from a per-overlay `LANGFUSE_TRACING_ENVIRONMENT`
      (image is env-agnostic; NODE_ENV can't be used). Never create a second project per env.

### 4. Multi-modal logging (when the product handles non-text)
- [ ] Log visual inputs (images/diagrams), audio, and function-call payloads as the
      **input of a generation** (e.g. figure captioning → generation with the image
      data-URI). The SDK uploads media to the Langfuse blob store (controller MinIO
      `10.0.0.1:9000`) → **needs a host-scoped egress rule** (else `fetch failed`,
      only a broken media ref logs). Best-effort; never fail the main flow.

### 5. Prompt Management (decoupled, label-routed) — MANDATORY, not optional
- [ ] **Decoupled deployment:** system prompts / few-shot / output schemas live in the
      Langfuse project, NOT hardcoded in Git. The Git copy is the **seed + runtime
      fallback** (Langfuse-first, fall back to the committed template — prompt
      management must never be a runtime SPOF).
- [ ] **Dynamic label routing:** pull by **label**, not pinned version, via a
      per-overlay `LANGFUSE_PROMPT_LABEL` (**prod=`production`**, **dev=`latest`**;
      `canary` optional) → zero-downtime rollout/rollback by relabelling, no redeploy.
      One project serves both envs.
- [ ] **Mustache + typing:** template vars are `{{var}}`, compiled via `prompt.compile()`
      with the declared variable set (store the variable list in the prompt `config`).
      Keep message *structure* (history/user turn) in code; render the managed system
      text as a **literal** message so compiled content isn't re-parsed.
- [ ] **Trace-linked attribution:** pass the resolved Langfuse prompt object as
      `prompt` on the generation → every call links the exact prompt **version**
      (A/B testing + regression attribution).
- [ ] **Playground:** once prompts are in Langfuse, non-devs (PM/domain experts) can
      tweak templates + params and test against real trace data — no code needed.

## Reference wiring (retrieva)
- Tracing + prompt fetch: `retrieva/backend/config/tracing.js` (`startTrace`,
  `getLangfusePrompt`), `config/promptManager.js` (`resolveRagPrompt`, Git fallback).
- Prompt seed/fallback: `backend/prompts/ragPrompt.js` (`RAG_SYSTEM_TEMPLATE`,
  `buildRagChatPrompt`). Instrumented flow: `services/rag.js`, `services/fileIngestionService.js`,
  `services/visionService.js`.
- Env (per overlay): `LANGFUSE_TRACING_ENVIRONMENT`, `LANGFUSE_PROMPT_LABEL`,
  `LANGFUSE_BASE_URL`, keys. Cost watch: PrometheusRule `cost.ai-vision`
  (`litellm_spend_metric_total{requested_model,team}`).

## Gotchas (learned, don't relearn)
- **ESO SSA no-op:** adding keys to an existing ExternalSecret silently no-ops under
  ArgoCD SSA → delete the ES to force a fresh render.
- **LiteLLM team access = grant by model NAME** in `manifests/ai/40-key-seeder.yaml`
  (built-in eu/us/onprem groups don't auto-expand); re-run the seeder Job.
- **Prod promotion goes through Kargo**, never a manual overlay `newTag` edit — promote
  the dev-verified Freight → Kargo opens the CODEOWNERS PR → squash-merge.
- **ClickHouse system logs (no TTL) fill the Langfuse PVC** → all traces dropped
  (code 243). Disable the query profiler; a `<ttl>` in CH *config* crashes it. See
  `[[feedback_langfuse_clickhouse_syslog_pvc_full]]`.
