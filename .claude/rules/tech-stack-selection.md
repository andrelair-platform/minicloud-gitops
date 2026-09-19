# Tech-Stack Selection (project onboarding)

**Principle: choose the best-fit stack per project from the approved palette — do NOT default every
service to one language.** Go is a fine choice for some services; it is not the house default. A varied,
fit-for-purpose stack is deliberate (it matches real enterprise IS reality and shows breadth). Pick per
workload, record *why*, and name the stack in the architecture — an unnamed "service" is an incomplete
design artefact.

## Approved palette

**Backend / API**
- **Java / Spring Boot** — heavy transactional/auditable domains; enterprise-insurance classic
- **Go** — high-throughput, low-latency, small-footprint services, infra/CLI/agents-glue
- **Python** — **FastAPI** (typed APIs, default), **Django** (batteries-included, admin/ORM-heavy apps), **Flask** (tiny services). Home turf for numeric/actuarial math (pandas/numpy) and AI/document pipelines
- **NestJS (TypeScript)** — structured, DI-based; great when you want one language across front + back
- **Express (TypeScript)** — lean Node services; **TypeScript first**, only a little plain JavaScript where unavoidable

**Frontend**
- **Next.js** (default) + **React** — the standard SPA/SSR choice
- **PWA** — add only when a mobile/offline experience is actually needed (no native app unless a real need)

> Datastore/eventing/secrets/etc. are the platform standard (Postgres · NATS · Temporal · ESO/Vault ·
> Authentik · cert-manager) regardless of the app language — this rule governs the **app** language/framework.

## Decision guide (heuristics, not laws)

| The workload is mostly… | Lean toward |
|---|---|
| Numeric pricing/rating, actuarial math, data/AI/document pipelines | **Python + FastAPI** |
| A heavy transactional domain, long-lived enterprise service | **Java / Spring Boot** |
| High-throughput / low-latency / tiny footprint, infra glue, agents | **Go** |
| One-language full-stack with the Next.js UI, structured API | **NestJS (TS)** |
| A lean webhook/BFF/integration shim | **Express (TS)** |
| A .NET-shop integration or a strong C# domain reason | **C# / .NET** |
| The user-facing app | **Next.js + React** (PWA if mobile/offline is real) |

Tie-breakers: consistency with a sibling service it integrates tightly with; solo-dev velocity; and where
the *hard part* of the domain lives (put the service in that ecosystem's home language).

## Record the choice (mandatory on onboarding)

1. **Decide** the backend + frontend from the palette using the guide above.
2. **Write an ADR** in the product's `docs/architecture/adr/` — *Context · Decision · Consequences* — so the
   "why" survives (e.g. "Python+FastAPI because pricing math + document extraction are Python-native").
3. **Name the stack in the architecture** — the C4 container diagram nodes and the component table state the
   language/framework (not just "service"), and the PRD/brief reference it.
4. This is a **BMAD onboarding gate item** (see `conventions.md` *Repo standardisation* + `bmad-compliance.md`):
   a Path-C product isn't "ready to build" until its stack is chosen, justified in an ADR, and shown in the
   architecture.

## Current picks (extend as products onboard)

| Product | Backend | Frontend | ADR |
|---|---|---|---|
| ktayl Underwriting & Pricing (#12) | **Python 3.12 + FastAPI + Pydantic** (SQLAlchemy/Alembic; numpy/pandas rating; Python extraction worker) | Next.js + React | `ktayl-underwriting/docs/architecture/adr` ADR-007 |
| Retrieva | Express 5 / Node 20 (TypeScript) | Next.js 16 / React 19 | (retrieva docs) |
| platform-demo · minicloud-plane · minicloud-agent/crew | Go / Python | — | — |

> Keep this table current when a new product picks its stack, so the palette stays a live portfolio view
> rather than a static list.
