# Proof Catalog — competency → concrete proof (target: 30–50 by end of year)

The portfolio index. Each row maps a competency to a **proof you can show** (case study / postmortem /
PR / live demo / eval) + its **evidence** (a number or an artifact). Groomed quarterly
(`.claude/rules/evidence-and-proof.md` + `productization.md`). Seeded with proofs already earned —
extend as you build. Status: ✅ proven · 🏗️ in progress · ⬜ planned.

| Competency | Proof (what + link) | Evidence (metric / artifact) | Status |
|---|---|---|---|
| Legacy integration | ACL + CDC + Strangler over GlobalCore → ktayl-claims | SOAP→JSON ACL, Debezium→NATS `CLAIMS_CDC` live | ✅ |
| Distributed systems | Durable JetStream ingest (ktayl-core Billing, ADR-003) | stream `UNDERWRITING_EVENTS` live; ack/term/nak consumer | ✅ |
| Event-driven architecture | HR J/M/L seam ERPNext→NATS→ktayl-iam | 98 tests; live dev+prod; one-durable discipline | ✅ |
| Backend / DDD | ktayl-core modular monolith (Spring Modulith) | `ApplicationModules.verify()` green in CI | ✅ |
| Backend / money domain | Billing premium→cash→GL (integer minor-units, outbox) | BILL-010/011 live; L1+L3 contract tests | 🏗️ |
| Idempotency | policy_number / client_key / webhook dedupe | replay = no-op (tested) | ✅ |
| Security / SoD | ktayl-iam four-eyes dual-approval + append-only audit | self-approval rejected; DB rewrite-rule audit | ✅ |
| Security / supply chain | cosign + SBOM + Trivy CRITICAL gate | gate **rejected** a stale Spring Boot (real catch) | ✅ |
| Security / secrets | Vault + ESO + PKI, KMS auto-unseal, 3-tier model | no plaintext secret in Git/images | ✅ |
| Platform / GitOps | ArgoCD auto-sync + CODEOWNERS prod gate | "never manual sync"; selfHeal proven | ✅ |
| Platform / promotion | Kargo git-Warehouse dev→prod | one immutable SHA promoted; squash-signed PR | ✅ |
| SRE / DR | CNPG + Velero restore drill; Vault raft snapshot | authentik restore ~9 min (RTO proof) | ✅ |
| SRE / reliability | SLO register + Game Days | _seed: run scenarios 03/04/08_ | 🏗️ |
| AI / LLMOps | LiteLLM gateway + Langfuse eval + Presidio DLP | per-product tracing; cost/req metered | ✅ |
| AI / RAG | Retrieva multimodal ingestion (Docling + VLM) | live dev+prod, cost-gated | ✅ |
| Data | Data Platform slice 1 (dbt + CNPG + Metabase) | policy_portfolio medallion from live PAS | ✅ |
| Architecture / ADR | ADRs with Options+Trade-offs (ktayl-core 001/002/003) | committed decision log | ✅ |
| Reliability under failure | **a postmortem from an induced Game Day** | _seed: first write-up pending_ | ⬜ |
| Communication | a published case study (LinkedIn/portfolio) | _seed: first post pending_ | ⬜ |
| Business / ROI | a productization step (brick → offer) | _seed: Q4 cadence_ | ⬜ |

**Gaps to close for a balanced dossier (highest interview value):** a real **postmortem from an induced
incident** (SRE), a **published case study** (communication), and a **first external validation**
(business). These three convert "I built it" into "I operate + explain + validate it."
