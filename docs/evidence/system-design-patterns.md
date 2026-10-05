# System-Design Pattern Catalog — ktayl-solution (interview prep)

Every pattern below is **implemented for real** on this platform, so you can answer a system-design
question with *"here's where I built it and the trade-off I hit"* instead of theory. Format per pattern:
**Problem → Trade-offs → Where in ktayl (the proof) → 30-second framing.** Keep this current as you build
(the discipline is in `.claude/rules/evidence-and-proof.md`). This is a **consulted** doc — study it
before interviews; it is not auto-loaded.

> How to use it in an interview: name the pattern, state the *problem* it solves, give **one trade-off**,
> then "I used it in ktayl for X — here's what happened." That arc (problem → trade-off → real proof)
> is the signal.

---

## A. Integration & legacy

### Anti-Corruption Layer (ACL) + Strangler Fig
- **Problem:** a legacy core (SOAP/MySQL/batch) can't be rewritten, but new domains must not inherit its model.
- **Trade-offs:** an extra hop + a translation layer to maintain vs a clean domain boundary + an incremental migration path (don't big-bang).
- **Where (proof):** `ktayl-claims` over the frozen `globalcore` legacy — SOAP→JSON at the ACL, CDC→NATS, a modern CQRS claims domain on top. The legacy is *strangled* domain by domain, not replaced.
- **Framing:** "The real enterprise problem isn't 'rewrite the legacy' — it's coexisting with it. I put an ACL in front of GlobalCore so the Claims domain speaks its own language and the legacy stays untouched."

### Change Data Capture (CDC)
- **Problem:** get data/events out of a legacy DB without the legacy app emitting events.
- **Trade-offs:** eventual consistency + CDC-infra (Debezium) + schema-drift handling vs zero legacy code change.
- **Where (proof):** Debezium → NATS JetStream (`CLAIMS_CDC` stream) feeding the claims domain; decode of `_minor`/Date/MicroTimestamp types ([[reference_debezium_server_nats_cdc]]).
- **Framing:** "CDC let me stream the legacy's changes into the new world without touching the legacy."

### API gateway / BFF (Backend-for-Frontend)
- **Problem:** a browser SPA shouldn't hold secrets or talk to many services directly.
- **Trade-offs:** an extra server tier vs server-held tokens + a UI-shaped API + one SSO seam.
- **Where (proof):** `ktayl-underwriting` Next.js **BFF** (server-side `API_URL`, the `bff-auth` shared lib doing OAuth2 client-creds), and the **LiteLLM** AI gateway as a model BFF.

---

## B. Distributed systems & messaging

### Event-driven + durable pub/sub
- **Problem:** decouple producers from consumers; survive a consumer being down.
- **Trade-offs:** eventual consistency + ordering/at-least-once semantics to reason about vs temporal decoupling + replay.
- **Where (proof):** **NATS JetStream** streams `HR_LIFECYCLE`, `UNDERWRITING_EVENTS`, `CLAIMS_CDC`, `POLICY_EVENTS`. A **JetStream stream captures even a core publish** → made the Underwriting bound-risk event durable with zero producer change (ktayl-core Billing ingest, ADR-003).
- **Framing:** "Core NATS is fire-and-forget; for a money chain I needed replay, so I put the subject on a JetStream stream and consumed it durably."

### Transactional outbox
- **Problem:** update my DB *and* publish/post to an external system without a distributed transaction.
- **Trade-offs:** a polling/drainer + an outbox table vs never a half-committed money move.
- **Where (proof):** ktayl-core Billing posts Journal Entries to ERPNext via a `ledger_outbox` (BILL-014) — billing state commits locally; the GL post drains + retries async.

### Idempotency & dedupe
- **Problem:** at-least-once delivery + client retries must not double-charge / double-create.
- **Trade-offs:** a dedupe key/table + careful key design vs safe retries.
- **Where (proof):** `policy_number`-keyed ingest, Stripe `client_key` + `webhook_event` id dedupe (BILL-011/013), HMAC-signed HR events, the IAM assignment idempotency.
- **Framing:** "Every consumer and every payment is keyed so a replay is a no-op — that's how you survive at-least-once."

### Consumer lag + backpressure + DLQ
- **Problem:** a burst or a slow consumer builds a backlog.
- **Trade-offs:** scale consumers (cost) vs drop/delay; term a poison message vs infinite redelivery.
- **Where (proof):** the ktayl-core consumer's **ack / term(poison) / nak(transient)** policy; **KEDA** scales consumers on lag; JetStream persists the backlog until drained.

### Saga / process orchestration
- **Problem:** a multi-step business transaction spanning services with no 2PC.
- **Trade-offs:** explicit compensation + an orchestrator (Temporal) vs implicit coupling.
- **Where (proof):** the Underwriting **bind 3-step lifecycle** (create→submit→activate the PAS, 409-as-success idempotency, best-effort event); the HR **J/M/L** flow; **Temporal** deployed for durable workflows.

---

## C. Domain & service architecture

### Modular monolith + bounded contexts (DDD)
- **Problem:** clean domain boundaries without the per-service tax (CI/CD/DB/netpol × N) for a solo team.
- **Trade-offs:** one deployable/one process (shared failure domain) vs enforced module seams + a cheap extraction path.
- **Where (proof):** `ktayl-core` (Spring Modulith) — `billing` module, schema-per-module, boundaries **enforced by `ApplicationModules.verify()`** in CI (ADR-001, `architecture-strategy.md`).
- **Framing:** "Microservices-from-day-one is a trap solo; I designed bounded contexts as *modules* with enforced boundaries, so extraction later is lift-the-schema, not untangle-the-ball."

### CQRS
- **Problem:** read and write models diverge (a claims workbench reads differently than it writes).
- **Trade-offs:** two models + sync lag vs independent read/write scaling + fit-for-purpose views.
- **Where (proof):** `ktayl-claims` (command side + read projections, Postgres).

### Database-per-service / schema-per-module
- **Problem:** data isolation + independent evolution.
- **Trade-offs:** no cross-service joins (must integrate via API/events) vs strong isolation + the extraction escape route.
- **Where (proof):** every ktayl service owns its Postgres; ktayl-core uses schema-per-module.

---

## D. Platform, delivery & reliability

### GitOps / reconciliation (desired-state control loop)
- **Problem:** drift + "who changed prod?"; let many teams deploy without hand-access.
- **Trade-offs:** everything-through-Git latency vs auditability + self-heal + no manual kubectl.
- **Where (proof):** **ArgoCD** (auto-sync, selfHeal, prune) + **CODEOWNERS** prod gate; the control-loop pattern. "Never manual sync" is a rule ([[feedback_never_manual_argocd_sync]]).

### Progressive delivery (canary / blue-green)
- **Problem:** a bad release must not serve users.
- **Trade-offs:** slower rollout + analysis infra vs auto-abort on metrics.
- **Where (proof):** **Argo Rollouts** + analysis health-gates (auto-abort); the prod runtime brake.

### Multi-stage promotion (immutable artifact)
- **Problem:** promote the *same* artifact dev→prod, not rebuild per env.
- **Trade-offs:** promotion machinery (Kargo) vs provable "what's in prod = what passed dev".
- **Where (proof):** **Kargo** git-Warehouse (Freight = a commit; both images pinned to the SHA); the git-vs-image Warehouse decision (JVM base-layer date breaks NewestBuild) ([[reference_kargo_promotion]]).

### Golden path / self-service platform
- **Problem:** 20 teams shouldn't each reinvent (or break) deploy + security.
- **Trade-offs:** maintaining templates vs paved-road consistency + guardrails.
- **Where (proof):** **Backstage** scaffolder templates + the GAP wrapper-chart Helm golden path.

### SLO / error budget + RED/USE observability
- **Problem:** "is it reliable?" needs a measured answer.
- **Trade-offs:** instrumentation + target discipline vs an objective reliability signal.
- **Where (proof):** Prometheus/Grafana/Loki + the `sdlc_loop` control-band detector; the SLO register + Game Days (`reliability-and-gamedays.md`).

### Backup / restore + DR (RPO/RTO, multi-region)
- **Problem:** survive node/cluster/provider loss; a regulated insurer *must* (DORA Art. 11–12, 28–29).
- **Trade-offs:** backup cost + restore-drill effort vs provable recovery.
- **Where (proof):** **Velero** + **CNPG** backups (R2) + Vault raft snapshots; the authentik ~9-min restore drill; multi-cloud DR anchors (OCI/AWS free-tier) ([[feedback_cnpg_backup_restore_ops]]).

---

## E. Security & governance

### Zero-trust / identity-as-perimeter + default-deny network
- **Problem:** BYOD, untrusted devices — the network isn't the perimeter.
- **Trade-offs:** per-app SSO + netpol maintenance vs no implicit trust.
- **Where (proof):** **Authentik** OIDC on every app, **default-deny NetworkPolicies** + governed egress; `workplace-architecture.md`.

### Policy-as-code / admission control
- **Problem:** enforce rules (non-root, allowed registries, no hostname-pin) without trusting authors.
- **Trade-offs:** policy authoring + exemptions vs unbypassable guardrails.
- **Where (proof):** **Gatekeeper/OPA** constraints; + client-side Claude-Code hooks (`agentic-guardrails.md`).

### Secret management / dynamic secrets + PKI
- **Problem:** no secrets in Git/images; rotate; internal TLS.
- **Trade-offs:** Vault+ESO operational surface vs no plaintext secrets + auditable issuance.
- **Where (proof):** **Vault + ESO** (ExternalSecrets), Vault **PKI** (cert-manager ClusterIssuer), KMS auto-unseal; the 3-tier secret model ([[feedback_controller_secret_tiers_offcluster]]).

### Supply-chain security
- **Problem:** prove an image is what you built + has no known CRITICALs.
- **Trade-offs:** sign/scan/SBOM pipeline vs provable provenance + a CVE gate.
- **Where (proof):** keyless **cosign** + **SBOM** + **Trivy** CRITICAL gate (which correctly rejected a stale Spring Boot — ktayl-core BILL-010).

### Four-eyes / Separation of Duties (dual control)
- **Problem:** a single actor must not grant themselves sensitive access.
- **Trade-offs:** two approvers (latency) vs an SoD control + audit.
- **Where (proof):** `ktayl-iam` dual-approval (manager + role-owner, no self-approval) + append-only audit.

---

## F. Scaling & AI

### Autoscaling / scale-to-zero (event & HTTP)
- **Problem:** right-size on a 5-node lab; idle = 0.
- **Trade-offs:** cold-start vs cost; selfHeal-vs-autoscaler ownership of replicas.
- **Where (proof):** **KEDA** (HTTP add-on scale-to-zero on platform-demo; event-lag scaling on consumers).

### Enterprise LLM gateway + RAG + eval (governed AI)
- **Problem:** put an LLM into a regulated enterprise safely (cost, PII, prompt-injection, hallucination, audit).
- **Trade-offs:** a gateway hop + eval infra vs centralized policy/cost/audit + measurable quality.
- **Where (proof):** **LiteLLM** gateway (auth/budget/routing) → RAG (**Qdrant**) → **Langfuse** tracing + evals → **Presidio** DLP; the AI-Act gate + per-product LLMOps (`llmops.md`, `[[reference_per_product_llmops]]`).
- **Framing:** "An enterprise LLM feature is 20% the model and 80% the gateway: auth, cost control, PII redaction, evaluation, fallback and audit — that's what I built around it."

---

## Design drills (answer from what you built)
Rehearse these out loud; each maps to real proofs above:
1. **Design a claims system that stays consistent across services.** → DDD bounded context → `@Transactional` writes → domain events (JetStream) → idempotency keys → CQRS read side → outbox for external posts. *(ktayl-claims + ktayl-core)*
2. **Claims receives 10k events while it's down — what happens?** → JetStream persistence → consumer lag → KEDA scales consumers → ack/term/nak → DLQ for poison → replay on recovery.
3. **Integrate a legacy SOAP core without rewriting it.** → ACL (SOAP→JSON) + CDC→events + Strangler Fig per domain. *(ktayl-claims/globalcore)*
4. **Let 20 teams deploy without breaking the cluster.** → golden path (Backstage) + GitOps (ArgoCD) + RBAC + policy-as-code (Gatekeeper) + namespace quotas + per-team observability.
5. **Design DR for a regulated insurer.** → RPO/RTO targets → Velero + CNPG + raft snapshots → multi-region (OCI/AWS) → a restore *drill* with measured recovery.
6. **Put an LLM into an enterprise safely.** → gateway (auth/budget) → RAG → eval → PII redaction → prompt-injection defense → fallback → audit.
7. **Move one immutable artifact dev→prod with a human gate.** → Kargo Freight + CODEOWNERS PR + canary Rollout + the git-vs-image Warehouse trade-off.
8. **Turn a bound policy into cash reliably.** → event-driven ingest (durable JetStream) → invoice/installments (money as integer minor-units) → PSP webhook (signature-verified, idempotent) → transactional outbox → GL double-entry. *(ktayl-core Billing)*
