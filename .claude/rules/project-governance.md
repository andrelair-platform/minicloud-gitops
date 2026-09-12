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

**Owner = SA/TL**, approved at the **architecture spine review** + **security review** gates
(`bmad-compliance.md`). For the **cert**, these artefacts are evidence for **BC02 (concevoir)** /
**BC03 (déployer & sécuriser)** — the threat model + NFR register especially.

**Reference implementation:** `retrieva/docs/docs/architecture/solution-architecture.md` (assembles
retrieva's existing architecture/ + security/ docs into the set + C4 + NFR register + threat model +
ADR log). Copy its shape for a new Path-C product.

## Applied projects

| Project | Document | Status |
|---------|----------|--------|
| ktayl Claims & Policy Platform (CERT-1) | `docs/certification/01-cahier-des-charges-fonctionnel.md` section 15 | ✅ Done (RACI) |
| Retrieva (RNCP39583) | `retrieva/docs/docs/architecture/solution-architecture.md` | ✅ SA artefact-set reference |
