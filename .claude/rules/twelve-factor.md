# Twelve-Factor — the app/process contract (what every custom service must satisfy)

[12factor.net](https://12factor.net) is the baseline discipline for every **custom-built service** on the
platform. Most factors are already given to us by the platform (ArgoCD + Kargo + ESO/Vault + CNPG); a few
are **app-behaviour** factors a service author must get right. This rule states each factor **as it applies
here** — the standard, who enforces it, and the current status — so a new service is checked against it at
onboarding (a DoD / New-Repo item, `conventions.md` + `bmad-compliance.md`), not rediscovered later.

**Scope.** 12-factor governs the **stateless app/process layer**. **Stateful platform services are
*backing services*, legitimately exempt** from the stateless-process purism of #6/#8/#9 — CNPG clusters,
Longhorn-backed singletons, vendor charts (ERPNext/GLPI/…) are *attached resources*, not 12-factor apps.
Don't contort a database into "a stateless process."

## The twelve, mapped to this platform

| # | Factor | The standard here | Enforced by / status |
|---|---|---|---|
| 1 | **Codebase** | one repo per app/product, **trunk-based `main`**, many deploys from one artifact. Shared code is a **published dependency** (e.g. `bff-auth` on GH Packages), never copy-paste. | branch strategy (`ci-registry.md`), Kargo one-artifact promotion. ✅ |
| 2 | **Dependencies** | declare + **pin/lock** everything (`go.mod`, `pyproject`, lockfiles, `Chart.lock`); isolate in the image. **Pin CI tools** where reproducibility matters — *exception:* security **scanners** (gosec/govulncheck) may stay `@latest` for newest rules/vuln-DB (a deliberate trade-off, note it). | lockfiles committed; Renovate/Dependabot; `17-dependency-auditability`. ✅ (scanners `@latest` is accepted) |
| 3 | **Config** | config in the **environment** via **ESO→Vault**; **never in git** (secrets blocked by `guard-write.py`); images are **env-agnostic** (read config at runtime — the Kargo prerequisite; `window.__ENV__` for Next). | ESO/Vault (`gitops.md`), `guard-write` hook. ✅ **strength** |
| 4 | **Backing services** | Postgres/NATS/Qdrant/Redis/MinIO/R2 are **attached resources** reached by a **URL/host in env** — swappable without code change. **CNPG per workload** is the DB standard (`schema-erd.md`, CNPG ADR). | proven by the Langfuse/Synapse `host:`-cutover migrations. ✅ **strength** |
| 5 | **Build, release, run** | CI builds an **immutable SHA image** (build) → **Kargo** promotes it (release = build + config) → **ArgoCD** runs it. Releases are immutable + versioned; **never edit a running release** (no manual tag edits — `gitops.md`). | CI + Kargo + ArgoCD + CODEOWNERS. ✅ **strength** |
| 6 | **Processes** | **stateless, share-nothing**; ALL state in backing services. **No in-process session/cache that breaks multi-replica** — session stores, caches, locks go to Postgres/Redis/NATS. | review; reference fix = `ktayl-iam` PG-backed `connect-pg-simple` sessions (the MemoryStore bug). ⚠️ author-owned |
| 7 | **Port binding** | the service is **self-contained** (ships its own HTTP server) and **exports via one port**, exposed through a Service/Ingress. No runtime-injected webserver. | library wrapper chart / Ingress. ✅ |
| 8 | **Concurrency** | **scale horizontally** (replicas), not by fattening one process. **Workers scale on queue lag** (KEDA-on-NATS) — need-first. Prod HA = 2–3 replicas (`gitops.md`). | KEDA (`11-keda-cron-scale-to-zero`), prod `patch-replicas`. ⚠️ mostly static today |
| 9 | **Disposability** | **fast startup**, **graceful SIGTERM shutdown** (drain in-flight, close DB/NATS), **robust to sudden death** (idempotent work, JetStream redelivery). Handle SIGTERM (NestJS `enableShutdownHooks`, Go signal ctx, FastAPI lifespan). Keep startup light. | review; relates to migrations-on-boot (startup cost, see #12). ⚠️ author-owned |
| 10 | **Dev/prod parity** | exactly **2 envs** (dev+prod), the **SAME artifact promoted** (never rebuilt per-env), **same backing-service types + major version** (Postgres **17** everywhere — CNPG 17, CI test DBs 17, tbls 17.4). **Real DB in L2 tests** (no mocks-only — `testing.md`). | Kargo; the PG16→17 parity fix; testcontainers/service-PG. ✅ **strength** |
| 11 | **Logs** | emit to **stdout** as an **event stream** → Promtail/OTel → Loki. The app **never** manages log files/rotation, and **never disables its own loggers** (the alembic `fileConfig` incident — `testing.md`/`qa-gate.md`). | OTel/Promtail/Loki. ✅ **strength** |
| 12 | **Admin processes** | one-off tasks (seeds, dbt runs, provisioners, backups) run as **Jobs/CronJobs** in the **same image + env**. **Schema migrations** are the documented exception — currently **self-migrate on boot** (ADR `docs/migrations-on-boot.md`), with a revisit trigger → a **same-image `initContainer`**. | CronJobs/Jobs; the migrations ADR. ⚠️ migrations = deliberate exception |

## The three the author must actively get right (the rest are platform-given)
- **#6 stateless** — no in-memory session/cache/lock shared across replicas (→ Postgres/Redis/NATS).
- **#9 disposability** — SIGTERM handler + drain; idempotent consumers; light startup.
- **#12 admin processes** — migrations/seeds/one-offs as Jobs or a same-image entrypoint, not woven into request handling (migrations-on-boot is the one accepted, documented exception).

## Beyond 12-factor (already standard here — don't treat as optional)
Telemetry/observability (Prometheus/Grafana/Loki/OTel + LLMOps `llmops.md`), **auth/SSO** (Authentik, never app-local auth), **API-first** (committed `openapi.yaml` + L3 contract tests), and **supply-chain** (cosign/SBOM/Trivy) are the modern additions the 2011 list omits — they are mandatory on this platform, not extras.

## Don't
- Don't put session/cache state in process memory on a multi-replica service (#6).
- Don't bake env into an image or read it only at build time (#3) — breaks Kargo promotion.
- Don't hand-edit a running release's image tag (#5) — Kargo owns promotion.
- Don't manage log files or silence loggers in-app (#11).
- Don't weave migrations/admin work into the request path (#12) beyond the accepted boot-migration exception.

Related: `gitops.md` (build/release/run + Kargo + env-agnostic), `conventions.md` (config, repo standard),
`schema-erd.md` + `docs/migrations-on-boot.md` (data layer), `scheduling.md` (#8 placement),
`reliability-and-gamedays.md` (#9 under failure), `testing.md`/`qa-gate.md` (#10/#11 proof), `llmops.md`.
