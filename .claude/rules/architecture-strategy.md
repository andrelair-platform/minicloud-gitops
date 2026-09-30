# Architecture Strategy — service granularity (modular-monolith-first)

**Default for ktayl-solution IS business domains: a modular monolith, not a service per domain.**
*Design service boundaries from day one; do not DEPLOY them as separate services from day one.*
Full rationale + the current-state review: ADR `docs/modular-monolith-first.md`. This is the
auto-loaded rule that must change build decisions. (Scope: insurance **business** domains — not
platform infra, not the AI/data products, which are governed separately.)

## The rule
- A **new insurance business domain** (distribution, finance, compliance, dms, itsm, reinsurance,
  risk-engineering, international-programs, mdm, billing, …) is built as a **module inside
  `ktayl-core`** — `src/<domain>/` with its own API/interface + its own logical data boundary
  (schema-per-domain in one Postgres) — **NOT** a new repo / service / board / Kargo pipeline.
- **Do NOT create a new service, repo, or board for a business domain** without running the
  **extraction decision test** (ADR) and getting **several "yes"**: independent deployment · other
  team owns it · very different scaling · **different tech stack (e.g. Python/ML)** · strong data
  isolation · different SLA · consumed by several apps · clear stable business boundary. One or two
  yes ≠ a service. This is a **security/architecture-boundary decision** → the governance gate
  (`bmad-compliance.md`), recorded in an ADR.
- **The 4 existing services are deliberate, justified extractions, kept — not the default:**
  `ktayl-iam` (company-wide identity, consumed by all), `ktayl-claims` (ACL/Strangler over the
  frozen `globalcore` legacy — different stack + lifecycle), `ktayl-underwriting` (Python/FastAPI —
  pricing math is Python-native). `ktayl-policy-service` (Go/gRPC core PAS) is kept but is **the
  coupling seam to watch** (underwriting calls it synchronously 3× at bind).

## Module discipline (what keeps ktayl-core a modular monolith, not a big ball of mud)
- **High cohesion, low coupling + SRP** — one module = one business capability, one reason to change.
- **Talk via the interface, in-process** — a module calls another module's **public interface** (a
  function call) or an **in-process domain event** — never another module's internals, never another
  module's **tables**, and **never intra-monolith HTTP/queues** (that rebuilds the distributed
  monolith inside the app).
- **One Postgres, schema-per-module** — shared runtime + DB for simplicity, but isolated schemas so a
  module never reads another's tables → low coupling **and** the extraction escape-route stays open
  (lift the schema + interface, don't untangle shared tables).
- **Layered / component patterns compose INSIDE a module** (API → domain → persistence). Real NATS
  events + a separate DB appear only when a module is actually **extracted** to a service.

## Anti-patterns (refuse / flag these)
- **Spinning up a new repo+board+service for a domain that has no team boundary and no scale
  pressure** — the "N-microservices-from-day-one" trap. For a **solo dev**, each service also drags
  the full per-service tax (CI + Kargo + CNPG + Helm + netpols + QA gate + docs + the SDLC harness).
- **Synchronous call chains between core domains** (e.g. `claim → policy → customer → billing` at
  request time) = a **distributed monolith** — the disadvantages of both. Prefer a module call
  (in-monolith) or an **async event/saga**; never a shared database across services.
- Confusing "microservices" with "good architecture": a strong modular monolith with real domain
  boundaries beats a chatty mesh of services.

## When a module DOES earn extraction
Follow the ADR's Phase 3: it graduates to a service (own repo/CI/Kargo/DB) only when the test
justifies it; the boundary designed up front is the escape route that makes it cheap.

Related: [[project_ktayl_solution_is]], [[project_ktayl_is_build_sequencing]], `tech-stack-selection.md`,
`conventions.md` (deploy-repo vs code-repo), `github-projects.md` (ktayl-core = one board, revisit).
