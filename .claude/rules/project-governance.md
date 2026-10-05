# Project Governance Standard

Every new project on the minicloud / ktayl-solution platform must include:

1. **A project card** — name, GitHub issue(s), phase, target delivery date
2. **Role mapping** — which of the 15 standard roles are active and who fills them
3. **A RACI matrix** — instantiated from the template in `project-governance/project-governance-standard`
4. **Out-of-scope roles** — explicitly listed with justification

This applies to: microservices, integrations, infrastructure components, data pipelines, AI features, and any workload that crosses more than one delivery phase (P1–P6).

## The 15 Roles (codes)

| Code | Role |
|------|------|
| STK | Stakeholder / Client |
| PM | Product Manager |
| BA | Business Analyst |
| UX/UI | UX/UI Designer |
| SA | Solution Architect |
| TL | Tech Lead |
| FE | Frontend Developer |
| BE | Backend Developer |
| DBA | Database Engineer |
| DO | DevOps / Platform Engineer |
| QA | QA Engineer |
| SEC | Security Engineer |
| SRE | Site Reliability Engineer |
| SUP | Support / Helpdesk |

## The 6 Delivery Phases

| # | Phase | Key deliverables |
|---|-------|-----------------|
| P1 | Initiation & Requirements | Business case, CdCF / functional spec |
| P2 | Architecture & Design | Technical architecture, wireframes, data model |
| P3 | Development | Frontend, backend, AI components, integrations |
| P4 | Infrastructure & CI/CD | Docker, Helm/Kustomize, ArgoCD, CI pipelines |
| P5 | Testing & Security | L1–L4 tests, SAST, AppSec, UAT |
| P6 | Release & Operations | Production deployment, monitoring, runbooks |

## RACI Legend

R = Responsible (does the work) · A = Accountable (owns outcome, approves) · C = Consulted (input before/during) · I = Informed (notified after)

## Where to put the RACI

- For certification projects: section 15 of the CdCF document
- For other projects: a `## Project Governance` section in the project's primary documentation page
- Template: `docs/project-governance/project-governance-standard.md`

## Solution Architecture artefact set (owner = SA/TL)

A Solution Architect delivers a **technically justified solution + the artefacts that let the org
build/operate/secure/evolve it** — not code. The named set below is the SA deliverable. It is
**planning context** (rationale, NFRs, threat model) → lives in the **product's own docs**
(`<repo>/docs/`), consulted in bursts; it is **not** the tiny per-repo `AGENTS.md` (see
`bmad-compliance.md` *Existing-codebase context*), and it does **not** restate the code.

**Scale by delivery path — this is Path C / boundary-crossing work, not every change.** Don't produce
a threat model + C4 for a one-line fix or a demo service. Required for a **new product / major
initiative**, or a change crossing a security/architecture boundary (see the governance gate in
`bmad-compliance.md`).

| # | Artefact | What it answers | 🔴 Path C / 🟡 Path B | Maps to |
|---|---|---|---|---|
| 1 | **Solution Architecture Document** (index) | how the whole thing fits together | 🔴 | the BMAD `architecture.md` spine (`/bmad-architecture`) |
| 2 | **C4 diagrams** — context → container → deployment | boundaries, components, where it runs | 🔴 context+container · 🟡 context | ASCII/mermaid in the product docs |
| 3 | **ADR decision log** (index of ADRs + status/owner) | *why* it's like this, 6 months later | 🔴 | existing ADRs (`docs/*.md`) indexed in a register |
| 4 | **NFR register** | SLOs, scale, availability, RTO/RPO, security, observability | 🔴 | the PRD NFR section (#1088) made measurable |
| 5 | **Threat model** (STRIDE-lite + mitigations) | trust boundaries, attack surface, controls | 🔴 (boundary changes) | feeds the **security review** gate |
| 6 | **Integration / data-flow design** | APIs, events, data ownership, residency | 🟡 when it integrates / holds PII | data-flow + API contracts |
| 7 | **Data design** — schema + **ERD** + migration strategy | the data model, ownership, how it evolves | 🔴 **if it has a DB** | a mermaid `erDiagram` + the schema + Flyway/Alembic migrations (the per-repo `data-model/` MCD→MLD→MPD) |
| 8 | **API specification** — the contract | endpoints, request/response, errors, auth, idempotency | 🔴 **if it exposes an API** | a committed **`<repo>/api/openapi.yaml`** (+ the `documentation.md` endpoint rule + the L3 contract tests in `testing.md`) |

**The SDD = artefact #1 assembled.** A **System Design Document** is not a separate deliverable — it is
the **Solution Architecture Document (#1)** assembled from #1–#8 into one per-product blueprint (the
single source of truth). It maps 1:1 to the standard SDD checklist: **Requirements/NFR** (#4 + the PRD) ·
**System architecture / C4** (#2) · **Data design / ERD** (#7) · **API spec** (#8) · **Operational &
scaling** (SLOs in `reliability-and-gamedays.md` + envs/promotion in `gitops.md`) — **plus** the extras a
standard SDD lacks: ADR log (#3), threat model (#5), compliance + cost (the PRD). Template:
**`docs/templates/sdd-template.md`**. Scale by delivery path — a full SDD is Path-C (new product / major
initiative), not a one-line fix. Docs-as-code (Markdown + Docusaurus + Mermaid in Git) is the house
tooling — no Confluence/Notion.

**Owner = SA/TL**, approved at the **architecture spine review** + **security review** gates
(`bmad-compliance.md`). For the **cert**, these artefacts are evidence for **BC02 (concevoir)** /
**BC03 (déployer & sécuriser)** — the threat model + NFR register especially.

**Reference implementations:** `retrieva/docs/docs/architecture/solution-architecture.md` (assembles
retrieva's architecture/ + security/ docs into the set + C4 + NFR register + threat model + ADR log) and
`ktayl-core/docs/architecture/solution-architecture.md` (the SDD template worked end-to-end: Requirements/
NFR · C4 · **Data design + ERD** · **OpenAPI** · operational/scaling · ADR log · threat model, assembling
its PRD + architecture + ADR-001/002/003 + SPEC). Copy either for a new Path-C product.

## Applied projects

| Project | Document | Status |
|---------|----------|--------|
| ktayl Claims & Policy Platform (CERT-1) | `docs/certification/01-cahier-des-charges-fonctionnel.md` section 15 | ✅ Done (RACI) |
| Retrieva (RNCP39583) | `retrieva/docs/docs/architecture/solution-architecture.md` | ✅ SA artefact-set reference |

## IS scope boundaries (deliberate — documented, not gaps)

A well-architected IS is defined as much by what it **deliberately excludes** as by what it builds.
These are **explicit, justified scope decisions** for the ktayl-solution IS — a boundary here is an
*accepted risk with compensating controls + a revisit trigger*, not an oversight. State them so an
auditor/interviewer sees intent, not incompleteness.

### BYOD — no managed physical endpoints (since 2026-09-15)
> This is the **scope decision** (what's out of scope). The **positive build principle** it forces —
> how every app must therefore be built (browser-first, data-server-side, identity-enforced) — is
> `workplace-architecture.md`. Read them together.

**Decision:** ktayl manages **no company computers, phones, or desk telephony**. Employees use their own
laptop/phone; access is **browser-first**. Device fleet / MDM-UEM (Intune-equivalent), endpoint
hardening, and hardware asset lifecycle are **OUT of scope for now**.

**Why it's coherent:** the whole digital workplace is already **web apps behind Authentik SSO + MFA**,
reached over Tailscale/Cloudflare — an inherently BYOD / zero-trust shape. Not managing endpoints fits
the architecture rather than fighting it.

**What we give up (the accepted risk):** remote wipe / lost-device response, guaranteed disk encryption,
endpoint hardening, device-level DLP (data can reach personal storage), asset lifecycle.

**Compensating controls — identity IS the perimeter:** MFA everywhere; every app SSO-gated (Authentik);
access only via Tailscale/Cloudflare; browser-first to minimise data-at-rest; app/gateway DLP (Presidio
+ default-deny egress netpols); session controls. This is the answer to *"how do you secure access with
no managed devices?"*

**Domain impact:** Enterprise IT (#12) → endpoints/MDM/Intune/telephony **out of scope**; ITSM/CMDB
(#16, GLPI) → CMDB scopes to **software/services/logical + cloud assets**, not a hardware fleet (cleaner);
IAM/IGA (#17) → becomes **the** primary control (more important, not less); threat model → "lost personal
device / endpoint compromise" is an **accepted, documented** risk.

**Revisit trigger:** bring endpoints in-scope when there are **real employees + PII at volume**, a real
audit, or a production-grade DORA-compliance claim. The self-hosted-fit successor is **Fleet/osquery** or
a UEM — not before the need is real (apply the `cloud-adoption.md` need-first gate).
