# Productization Backlog — bricks → products

Per `.claude/rules/productization.md`. The platform is the factory; these bricks are the sellable/
portfolio-grade products. Sell a brick, never "Minicloud". Each passes the `cloud-adoption.md` gate if it
uses real cloud. Status: ⬜ idea · 🏗️ shaping · 🧪 piloting · 💶 first-revenue.

| Brick (built) | Product | First form | Level | Status |
|---|---|---|---|---|
| LiteLLM gateway + Qdrant RAG + docs | **Private Enterprise AI Platform** (SSO + gateway + RAG + audit) | consulting install | 1 | ⬜ |
| Retrieva DORA / vendor-risk slice | **DORA Vendor-Risk AI** (supplier → evidence → AI score → dashboard) | B2B SaaS | 3 | 🏗️ (cert pilot) |
| ACL/CDC/CQRS (ktayl-claims) | **Legacy modernization mission** | consulting | 1 | ⬜ |
| Backstage + GitOps golden paths | **Internal Developer Platform** setup | consulting/package | 1–2 | ⬜ |
| Observability + SLO + Game Days | **Reliability/observability package** | package | 2 | ⬜ |
| cosign/SBOM/Trivy/Gatekeeper | **Supply-chain security hardening** | package | 2 | ⬜ |
| Velero/CNPG/multi-cloud DR | **DR architecture for critical workloads** | consulting | 1 | ⬜ |

**Strongest standalone SaaS:** DORA Vendor-Risk AI — a real, dated regulatory need (DORA in force; most
firms failed the 2024 ESA dry-run, [[reference_dora_market_validation]]); reuses Retrieva's graph.

## Quarterly proof cadence (the anti-"0 users" guard)
| Quarter | Proof | Target |
|---|---|---|
| Q1 — Engineering | the spine runs end-to-end | ✅ (Policy/Claims live, UW dev, Billing building) |
| Q2 — Production | survives incidents | Game Days + postmortems + met SLOs |
| Q3 — Business | external people use a brick | 5–20 experts test one brick (validation-log) |
| Q4 — Commercialization | someone will pay | a first transaction (€50–€500; the learning, not the amount) |
