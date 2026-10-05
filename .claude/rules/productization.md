# Productization — the platform is the factory; the bricks are the products

Don't try to sell "Minicloud" — a whole private cloud is unsellable against the hyperscalers. **The
*bricks* built on it are the monetizable/portfolio-grade products.** The platform is the **laboratory
that generates** portfolio, case studies, skills, contacts and (maybe) first revenue. This rule keeps
that honest and paced — it is Q3/Q4 work (after the evidence foundation of `synthetic-enterprise.md` +
`reliability-and-gamedays.md` + `evidence-and-proof.md`), not a day-one distraction.

## Brick → product map (seeded; register `docs/productization/product-backlog.md`)

| Platform brick | Candidate product | Easiest first form |
|---|---|---|
| AI Gateway (LiteLLM) + RAG (Qdrant) + docs | **Private Enterprise AI Platform** (SSO + gateway + RAG + audit) | consulting install |
| DORA / vendor-risk (Retrieva slice) | **DORA Vendor-Risk AI** (supplier → evidence → AI risk score → dashboard) | B2B SaaS |
| Legacy→modern (ACL/CDC/CQRS, ktayl-claims) | **Legacy modernization mission** | consulting |
| GitOps + golden paths (Backstage) | **Internal Developer Platform** setup | consulting/package |
| Observability + SLO + Game Days | **Platform observability / reliability package** | package |
| Supply chain (cosign/SBOM/Trivy/policy) | **Supply-chain security** hardening | package |
| DR (Velero/CNPG/multi-cloud) | **DR architecture for critical workloads** | consulting |

The **DORA Vendor-Risk AI** is the strongest standalone B2B SaaS candidate (a real, dated regulatory need
— DORA in force; most firms failed the 2024 ESA dry-run, see `[[reference_dora_market_validation]]`), and
it reuses Retrieva's graph. Treat Retrieva as the cert deliverable **and** the productization pilot.

## The three monetization levels (test in order; don't skip)
1. **Consulting / freelance** — "I'll stand up a private Enterprise AI Platform for you" (one brick, delivered).
2. **Productized service** — a fixed package (deploy + SSO + gateway + RAG + monitoring + security + docs)
   + monthly maintenance. *(Prices are formats to test, not market truths.)*
3. **SaaS** — e.g. DORA Vendor-Risk AI. Highest leverage, most work.

## The quarterly proof cadence (the anti-"12 months, 0 users" guard)
The main risk is **building for 12 months with nobody using anything** (100 technos / 0 users / 0 revenue).
So each quarter must produce a **different kind of proof**:

| Quarter | Proof | Concretely |
|---|---|---|
| **Q1 — Engineering** | the platform works | the spine runs end-to-end on dev/prod |
| **Q2 — Production** | it survives incidents | Game Days + postmortems + met SLOs (`reliability-and-gamedays.md`) |
| **Q3 — Business** | external people use a brick | 5–20 experts test the Claims Workbench / an AI brick |
| **Q4 — Commercialization** | someone will pay | a first transaction, even €50–€500 — the point is the *learning*, not the amount |

## External validation / pilot log (the one honest "real user" layer)
Recruit **5–20 real domain people** to test a **single brick** (30 min). Log each in
`docs/productization/validation-log.md`: who (role, not PII) · brick · date · feedback (workflow/UX/
vocabulary/gaps) · changes made. This yields **expert validation** — a different, honest proof than
"production usage" (never claim the latter; see the simulation disclaimer in `synthetic-enterprise.md`).

## Discipline
- **Sell a brick, never the platform.** The product is the AI Platform / the DORA SaaS — not "my k8s".
- **Honesty first** — simulation is disclaimed; validation ≠ traction; test-mode payments are test-mode.
- **A product is a proof too** — every productization step is a proof-catalog entry (`evidence-and-proof.md`)
  under Business/ROI + Communication.
- Any real cloud resource for a product still passes the `cloud-adoption.md` gate (free-tier, destroyable).
Related: `evidence-and-proof.md`, `synthetic-enterprise.md`, `[[reference_dora_market_validation]]`, `[[project_ydays_directeur_candidature]]`.
