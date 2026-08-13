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

## Applied projects

| Project | Document | Status |
|---------|----------|--------|
| ktayl Claims & Policy Platform (CERT-1) | `docs/certification/01-cahier-des-charges-fonctionnel.md` section 15 | ✅ Done |
