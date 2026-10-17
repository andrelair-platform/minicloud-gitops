# Documentation Standard — the taxonomy map (what docs exist, where they live, when they're required)

This is the **catalog/map** of every documentation category the platform produces, *mapped onto the homes
that already exist here* — it is NOT a new folder tree and does NOT duplicate the detailed rules. Pair it
with `documentation.md` (the **discipline**: docs-as-map, verified-reality, the DoD gate) — this file is the
**WHAT + WHERE + WHEN**, that file is the **HOW**.

> **Why this exists.** The platform already implements ~the full FAANG documentation taxonomy (Product ·
> Architecture · Developer · API · Quality · Operations · Security/Compliance · Business/Lifecycle · AI),
> but the knowledge was spread across 7 rules + the docs site, so no one could see the whole system at a
> glance or answer *"for this change, which docs are required?"*. This is that single view.

## Two orthogonal axes first (don't flatten them)
1. **Platform vs IS** (`platform-vs-information-system.md`) — a doc belongs to the **Platform** pillar
   (shared capability) or the **IS** pillar (a business app). Platform-level docs are cross-cutting
   (one copy, e.g. `gitops.md`, the SLO register); product docs live **with the product** (`<repo>/docs/`).
2. **Delivery path** (`bmad-compliance.md` A/B/C/E) — the doc burden scales to the work, exactly like the
   SA artefact set. A one-line fix (Path A) writes ~nothing new; a new product (Path C) produces the full set.

**We do NOT impose the generic `docs/01-07/` flat tree.** It would duplicate the SA artefact set and fight
the docs-as-map model. Instead the taxonomy is a **path-gated checklist pointing at existing homes**, plus
the canonical per-product skeleton below.

## The category map — every doc type → its home here → required at which path

🔴 required · 🟡 when it applies · — n/a. "Home" is where the *detail of record* lives; the central docs
site always carries the **map/pointer** (`documentation.md`).

| # | Category (doc types) | Home of record here | A | B | C |
|---|---|---|---|---|---|
| 1 | **Product** — PRD, user stories, roadmap, functional spec, UX, release notes | BMAD `prd.md` + `/bmad-ux` (`DESIGN.md`/`EXPERIENCE.md`); roadmap = **GitHub Project board**; release notes = **release-please `CHANGELOG`** | — | 🟡 PRD if new design | 🔴 PRD (+UX if UI) |
| 2 | **Architecture** — C4, HLD/LLD, ADR, ERD, sequence | **SA artefact set** (`project-governance.md` #1–8) assembled as the **SDD** (`docs/templates/sdd-template.md`); C4 via `diagrams-as-code.md`/Structurizr; ADR → **auto-indexed**; ERD → **auto-generated** (`schema-erd.md`) | — | 🟡 context C4 + ADRs | 🔴 full SDD |
| 3 | **Developer** — README, setup, CONTRIBUTING, coding standards, repo structure, troubleshooting | `conventions.md` repo-standardization (README/LICENSE/CONTRIBUTING) + tiny `AGENTS.md` (`bmad-compliance.md`); the zero→prod runbook (central site) | 🔴 README | 🔴 | 🔴 (+ coding-standards if a team) |
| 4 | **API & integration** — OpenAPI, auth, webhooks, error catalogue, versioning policy | committed **`<repo>/api/openapi.yaml`** (SA #8) + **L3 contract tests** (`testing.md`); SSO = `security-enterprise/sso-authentik` | — | 🔴 if it exposes an API | 🔴 (+ error catalogue + versioning policy) |
| 5 | **Quality & testing** — strategy, test matrix, unit/int/e2e, acceptance, perf, security-test, known-issues | `testing.md` (L0–L4) + `qa-gate.md` (live L5) + `engineering-standards/testing-strategy`; known-issues = **GitHub issues**; perf = k6 | 🔴 tests | 🔴 tier layers | 🔴 (+ perf + the **traceability matrix**) |
| 6 | **Deployment & operations** — CI/CD, infra, config, deploy guide, runbooks, monitoring, DR, SLO/SLA | `gitops.md` + `delivery-workflow` + the **zero→prod runbook** + `ops-runbooks` + `reliability-and-gamedays.md` (SLO register + Game Days + DR drills) | 🟡 | 🔴 | 🔴 (+ runbooks + SLO + DR drill) |
| 7 | **Security / privacy / compliance** — threat model, security architecture, data classification, privacy, risk register, incident response, audit evidence | SA #5 threat model + P0–P3 data classes; **`ktayl-compliance`** obligations-register + resilience-testing-programme; IR = postmortem template + Game Day 06; audit = change-records | 🟡 by risk | 🟡 by exposure | 🔴 (threat model + data-class + IR) |
| 8 | **Business / lifecycle** — user guide, admin guide, support KB, postmortems, SLO dashboard, migration, EOL | postmortems (`reliability-and-gamedays.md`); SLO dashboard = **Grafana**; EOL = `cloud-adoption.md`; user/admin guide = product `docs/` | — | 🟡 | 🔴 postmortems; 🟡 user/admin guide |
| 9 | **AI-specific** — model card, dataset/lineage, evaluation report, prompt versioning, RAG doc, agent spec, guardrails, LLMOps/FinOps | `llmops.md` (tracing/prompt-mgmt/cost) + `ai-governance` matrix + `ai-act-gate`; reference = retrieva | — | 🔴 **if it calls an LLM** | 🔴 (+ model card + eval report) |

**The thin spots (known, fill on need — don't create empty files):** coding-standards (#3), API error-catalogue +
versioning policy (#4), user/admin guides (#8), risk register (#7), model card + dataset lineage (#9). Each
is a 🟡 checklist item — add it the day the product actually needs it, not pre-emptively.

## New practice 1 — requirement IDs + the traceability matrix (Path C; the enterprise signal)
Give every requirement a **stable ID** and thread it end-to-end so a change to one requirement shows exactly
what else must move. IDs: **`FR-###`** (functional) · **`NFR-###`** (non-functional) · **`SEC-###`** (security)
· **`AI-###`** (AI behaviour). Each requirement must be **observable** (a testable acceptance criterion, not
"must be fast"). Then one matrix threads: **requirement ID → architecture component → test file → pipeline
stage → evidence**. Template: **`docs/templates/traceability-matrix.md`**; it lives at
`<repo>/docs/traceability-matrix.md` and is a **Path-C Definition-of-Done item** (and part of the SDD).
Worked reference: **`ktayl-core/docs/traceability-matrix.md`**. The matrix answers the interview-grade
question: *"If SEC-001 changes tomorrow, which components, tests, pipelines and docs change?"*

## New practice 2 — the canonical per-product `docs/` skeleton (stop the per-product variance)
One reconciled layout for every product's `docs/` (reconciles the SA artefact set with the category
checklist above). Template + the full tree: **`docs/templates/product-docs-skeleton.md`**. The short form:
```
<repo>/docs/
  prd.md                      # (1) Product — the contract        [Path B/C]
  architecture/
    solution-architecture.md  # (2) the SDD (assembles #1–#8)      [Path C]
    adr/                      #     decision records → auto-indexed
    c4-container.md           #     C4 (diagrams-as-code)
  data-model/                 # (2/7) tbls ERD → auto-generated    [if it has a DB]
  api/openapi.yaml            # (4) the API contract               [if it exposes an API]
  traceability-matrix.md      # (5) requirement → component → test → pipeline   [Path C]
  specs/spec-<epic>/SPEC.md   # the per-epic implementation contract
  runbooks/ , slo.md          # (6) operations                     [if prod-grade]
  security/threat-model.md    # (7) security                       [Path C / boundary]
  ai/evaluation.md , model-card.md  # (9) AI                       [if it calls an LLM]
```
Everything else (CI/CD, GitOps, observability, secrets, SSO, backup/DR) is **platform-level** and
**referenced, not restated** — the product docs link the Platform standards (`gitops.md`, `llmops.md`,
`reliability-and-gamedays.md`, …), they do not copy them.

## Don't
- Don't impose the generic `docs/01-07/` tree, and don't restate a Platform standard in a product's docs — **link it**.
- Don't write a requirement you can't observe (no "must be secure" — give it an ID + a testable criterion).
- Don't pre-create empty files for the thin categories — they're `🟡 on need`, gated by the delivery path.
- Don't let the central map and the detail drift — the ADR + ERD **auto-indexes** keep #2 honest; the same
  discipline (`documentation.md` mandatory-pairing) applies to every new doc.

Related: `documentation.md` (discipline/DoD), `project-governance.md` (SA artefact set + SDD), `bmad-compliance.md`
(path gating + the audit-trail-committed-to-docs rule), `testing.md`/`qa-gate.md`, `reliability-and-gamedays.md`,
`llmops.md`, `schema-erd.md`, `diagrams-as-code.md`, `evidence-and-proof.md`, `platform-vs-information-system.md`.
