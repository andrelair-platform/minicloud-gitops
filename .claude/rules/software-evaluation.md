# Software Evaluation & Selection — how the organisation adopts a third-party tool

**The process for deciding to adopt any third-party software into the stack** — a self-hosted FOSS tool
or a SaaS. It is **assembled from the gates that already exist** (need-first, adopt-vs-build, the
governance gate) into one evaluate → score → select → decide chain; it does **not** re-implement them.

> **Two layers (never conflate — `platform-vs-information-system.md` + `github-projects.md`).** The
> **PROCESS** here is **IS organisational governance** — *how the insurer decides what software to run*
> → **BC01 (cadrage/pilotage)** cert evidence. The **EXECUTION + evidence** of a given evaluation lives
> in **Retrieva** — the DORA third-party-ICT / vendor-risk **product** that runs on the platform (its
> "onboard a new tool" engine: register → two-lane score → decision pack → DORA Art. 28/30 clauses,
> [[project_retrieva_tool_onboarding]]) → **BC02/BC03** product evidence. **ktayl-solution IS is
> Retrieva's first internal user** — the process is the *how*, Retrieva is the *tool of record* that runs
> it. The dogfooding loop is the bridge between the two layers, not a merge of them.

## When it applies (scale by delivery path — `bmad-compliance.md`)
- **Any NEW third-party tool** being brought into the Platform or the IS (self-hosted FOSS **or** SaaS).
- **Scale to the work:** a **Path-A** dev utility → lightweight (need + adopt-vs-build verdict + a
  one-line decision note). A **Path-C** core/boundary system (a datastore, an identity system, a claims
  engine, anything holding **P0–P3** data or crossing a trust boundary) → the **full** chain below.
- **NOT for:** something you *build* (that's `tech-stack-selection.md` + the `architecture-strategy.md`
  adopt-vs-build test, which may send you here or to a build), and not a re-run on an already-adopted tool
  unless a **re-evaluation trigger** fires (below).

## The decision chain — reuse each gate, don't re-create it

| # | Step | Reuses (the authoritative gate) | Output |
|---|---|---|---|
| 1 | **Need-first** | `cloud-adoption.md` — *name the gap or don't build it* | a one-line "because…" (the current gap it closes) |
| 2 | **Adopt-vs-build** | `architecture-strategy.md` — the extraction / adopt-vs-build test | verdict: **adopt** · build · extend an existing tool |
| 3 | **Shortlist (2–3)** | hard constraints below (sovereignty · FOSS · self-hostable · licence) | a longlist screened to the real contenders |
| 4 | **Weighted score** | the **scorecard** (`docs/templates/software-evaluation-scorecard.md`) | ranked candidates, objective |
| 5 | **PoC on dev** | the **real dev cluster** (actual Authentik SSO / Vault / netpol) — *not* a vendor sales demo | evidence it fits the golden path (or doesn't) |
| 6 | **Security / compliance review** | `bmad-compliance.md` governance gate + `observability/21-security-evaluation` + DORA class + data class (P0–P3) | SEC/SA sign-off (mandatory for P0–P3 / boundary-crossing) |
| 7 | **Decision record** | an **ADR** (Context · Options · **Trade-offs** · Decision · Consequences) + RACI (`project-governance.md`) | the committed "why", auditable |
| 8 | **Record in Retrieva** | the vendor-risk product (the tool of record) | the evaluation + score + decision pack + DORA Art. 28/30 clauses (the dogfooding evidence) |

## The weighted scorecard — sovereign-first, adapted to THIS stack
Full fillable matrix: **`docs/templates/software-evaluation-scorecard.md`**. The adaptation vs a generic
enterprise RFP: this is a **FOSS-first, self-hosted, sovereign, solo** stack, so **TCO = operational
burden, not licence negotiation**, and the "demo" is a **PoC on the dev cluster**, not a sales call.
Default criteria (re-weight per evaluation):

| Criterion | Why it weighs here |
|---|---|
| Need-fit / business fit | closes a *named* current gap (the step-1 litmus) |
| Self-hostable / **sovereignty** | EU-sovereign, offline-capable — the platform thesis (`datastore-selection.md`, `cloud-adoption.md`) |
| **FOSS / licence** posture | AGPL/commercial traps, re-licensing risk, exit cost |
| **SSO-able** (Authentik OIDC / forward-auth) | the identity-is-the-perimeter admission rule (`workplace-architecture.md`) |
| Golden-path fit: **Vault/ESO · GitOps · NetworkPolicy** | does it deploy the wrapper-chart way or fight it (`gitops.md`) |
| Observability hooks (Prometheus/Loki/OTel) | Day-2 operability |
| **DORA third-party-ICT** class + **data class (P0–P3)** | regulated-insurer obligation; drives the security review depth |
| **Exit / portability** | the `cloud-adoption.md` exit test — can we leave in one command? |
| Operational **TCO** | cluster footprint vs quotas (`manifests/quotas/`), maintenance burden (solo) |

## Scale & don't
- **Path-A utility:** steps 1–2 + a one-line note — **skip** the full scorecard/PoC/ADR.
- **Path-C / boundary / P0–P3 tool:** the **full** chain (scorecard + PoC + security review + ADR + the
  Retrieva record) — the security review (step 6) is **not optional** here.
- **Don't** duplicate the gates (reference them), run a full RFP for a FOSS dev utility, or adopt anything
  without first **naming the gap** (step 1). Don't skip step 6 for a tool touching PII/P0–P3 or a trust boundary.
- **Re-evaluation triggers** (re-run the relevant steps): a licence change · EOL/unmaintained · a CVE or
  incident · a DORA re-assessment · the need disappears → **retire** it (an adoption decision has an exit).

## Where the artefacts live
- **Template** → `docs/templates/software-evaluation-scorecard.md`; a filled scorecard + the ADR live in the
  owning product's `docs/` (or the IS docs for an org-wide tool), paired with an org-site map page
  (`documentation.md`).
- **The record of truth for a real evaluation** → **Retrieva** (register + score + decision pack + DORA clauses).
- **Published governance map** (follow-up): an IS-pillar page (`is/`) that summarises this process + links
  the ADRs and the Retrieva register.

Related: `cloud-adoption.md` (need-first + exit test), `architecture-strategy.md` (adopt-vs-build),
`bmad-compliance.md` (governance gate + compliance-by-design), `project-governance.md` (RACI + SA artefacts),
`tech-stack-selection.md` (the *build* path), `platform-vs-information-system.md` (the two layers),
`productization.md` (Retrieva = the DORA vendor-risk product), `evidence-and-proof.md` (the case study),
[[project_retrieva_tool_onboarding]], [[project_ktayl_solution_is]].
