# System Design Document (SDD) — <product>

> The **single source of truth** for one product's architecture: the Solution Architecture Document
> (`project-governance.md` artefact #1) assembled from artefacts #1–#8. **Assemble, don't duplicate** —
> each section links the authoritative doc (PRD / ADR / SPEC) and summarises it. Lives at
> `<repo>/docs/architecture/solution-architecture.md`. Path‑C (new product / major initiative); scale
> down for smaller work. Docs‑as‑code: Markdown + Mermaid in Git. References: retrieva + ktayl-core.

- **Product / repo(s):** · **Owner (SA/TL):** · **Status:** draft | reviewed | as‑built · **Date:**
- **Delivery path:** C (full) | B (subset) · **Board:** #

> **Write for the reader, in three views** (one doc, audience‑tagged): **Conceptual** (business/UX — for
> PM, stakeholder, new hire) · **Component** (how parts interact — for FE/BE engineers) · **Operational**
> (where it runs — for DevOps/SRE). A reader should find their perspective in <30s. **Diagrams over
> prose, plain language over jargon, the *why* not just the *what*.** (See *Documentation principles* at the end.)

## 1. Conceptual view — what it does & why it matters  *(for PM / stakeholder / new hire)*
Plain language, no jargon: the business problem, who it serves, the value it delivers, and where it sits
in the ktayl‑solution IS. A newcomer should understand the point before any diagram. → links the PRD / brief.

## 2. Requirements
### 2.1 Functional
The capabilities (bulleted or → link the PRD). 
### 2.2 Non‑functional (NFR register)
SLOs (latency/availability), scale, data volume/retention, **RTO/RPO**, security, observability, **cost/
footprint** (fits which namespace quota). → the measurable NFRs; the live targets live in
`reliability-and-gamedays.md` (SLO register).
### 2.3 Technical → user‑outcome translation *(makes the NFRs legible to non‑engineers)*
Every NFR/tech choice restated as the outcome a stakeholder cares about — this is how you explain the
architecture to a PM (and in an interview):

| Requirement | Technical choice | User / business outcome |
|---|---|---|
| Scalability | Kubernetes + KEDA | "handles a 10× day without slowdown" |
| Performance | caching / off‑request work | "the action returns in < 300 ms" |
| Reliability | SLO + canary + DR | "stays up through an incident; recovers in minutes, loses no data" |
| Security | Authentik SSO + TLS + netpol | "only authorised people/systems touch the data" |

## 3. System architecture (C4)  *(Component + Operational views — for engineers / DevOps)*
- **Context** (who/what it talks to) — mermaid `C4Context` or ASCII.
- **Container** (the deployable units + data stores + boundary ports) — mermaid/ASCII.
- **Deployment** (where it runs: ns, dev/prod, ingress, Kargo) — ASCII.
State the **boundaries** explicitly (what it owns vs integrates with).

## 4. Data design
- **Store choice + why** (Postgres/CNPG · schema‑per‑module · etc.).
- **ERD** — a mermaid `erDiagram` of the core entities + relationships.
- **Schema / migrations** — the migration tool (Flyway/Alembic) + strategy; money as integer minor‑units;
  append‑only/audit tables. → link the migrations dir.
- **Ownership + residency** — which data this product owns; PII class; where it must not leave.

```mermaid
erDiagram
  ENTITY_A ||--o{ ENTITY_B : has
  ENTITY_A { string id PK  string status }
  ENTITY_B { string id PK  string a_id FK }
```

## 5. API specification
- The committed contract → **`<repo>/api/openapi.yaml`** (link it).
- Per endpoint (the `documentation.md` rule): **auth · headers · request body + required fields ·
  validation errors · response shape · status codes · idempotency**.
- Inbound non‑SSO surfaces (webhooks) — how they're authenticated (signature) + made idempotent.
- Cross‑service contracts consumed → the L3 contract test that pins them (`testing.md`).

## 6. Operational & scaling strategy
- **Environments + promotion** — dev/prod, Kargo (git vs image Warehouse), CODEOWNERS gate (`gitops.md`).
- **Scaling** — replicas, KEDA/HPA, scale‑to‑zero; the latency target + how load is handled; caching (if any).
- **SLOs + error budget** — the service's row in the SLO register; the alerts.
- **Failure modes + rollback** — what happens when each dependency dies; the canary brake; the Game Day
  scenarios that exercise it (`reliability-and-gamedays.md`).
- **Backup / DR** — RTO/RPO + the restore drill.

## 7. Security & compliance
- AuthN/AuthZ (Authentik OIDC, group‑gated), secrets (ESO→Vault), network (default‑deny + governed egress).
- **Threat model** (STRIDE‑lite + mitigations) → link.
- **Compliance mapping** — DORA / GDPR / Solvency II / IFRS 17 / AI‑Act as applicable + the cert bloc.

## 8. Decision log (ADRs)
Index of the product's ADRs (id · title · status · the trade‑off it settled). → link `docs/architecture/adr/`.

## 9. Open questions / deferred
What's explicitly out of scope now + the revisit trigger (honest, not gaps).

## Documentation principles (how to write this — not optional)
- **Multi‑audience, three views** — Conceptual / Component / Operational, each tagged so a PM, an
  engineer and an SRE each find their part fast.
- **Diagrams over prose** — a **Mermaid** diagram (rendered, versioned in Git) beats paragraphs; *any*
  diagram beats none. Never ship stale static PNG/PowerPoint exports.
- **Consistent naming** — the *same* names across every diagram, the ERD, the API and the text (a service
  is called one thing everywhere).
- **The *why*, not just the *what*** — justify the major decisions (→ the ADR log, §8).
- **Plain language + the translation table** (§2.3) — translate jargon into user outcomes.
- **Accessible + living** — give each diagram **alt text / a one‑line caption**; keep it **as‑built**
  (update in the same effort as the change — the `documentation.md` DoD gate). *A living doc people read
  beats a "perfect" one no one opens.*
- **The reader test** — hand it to someone who doesn't know the system: can they say what it is, operate/
  verify it, and act on it without asking you? If not, it isn't done.

Each section is evidence for the proof‑catalog (`evidence-and-proof.md`) + cert BC02/BC03. Tooling is
docs‑as‑code (Markdown + Mermaid + Git) — the house standard; no Confluence/Notion.
