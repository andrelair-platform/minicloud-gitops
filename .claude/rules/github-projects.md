# GitHub Projects — Issue Tracking Rules

## The two-layer model (ALWAYS keep this distinction — do not conflate)

The insurance IS and the certification project are **two different things**. Never treat
ktayl-solution as "the certification" or Retrieva as "just another platform app":

| Layer | What it is | Role |
|---|---|---|
| **ktayl-solution IS** | The insurance organisation's information system (minicloud platform + business apps) | The **organisational/business context** — the "company" and its infrastructure. Ongoing, real, needed. |
| **Retrieva** | The owner's **RNCP39583 certification project** | The **deliverable defended for the diploma** — a real DORA-compliance product that *runs on and benefits from* the insurance IS. |

**Consequences:**
- Certification **project = Retrieva** (per the #282 pivot); the ktayl-solution IS is its
  **organisational context**, not the cert itself.
- **Project-level** cert evidence (BC02 concevoir/développer, BC04 optimiser — accessibility/RGAA,
  cahier de recettes, manuels, MCO) is drawn from **Retrieva**. **Org-level** evidence (BC01
  cadrage/pilotage — CdCF IS, budget, governance) is drawn from the **ktayl-solution IS** as context.
- Bloc names are the **#282 authoritative** set: **BC01 Piloter · BC02 Concevoir & développer ·
  BC03 Déployer & sécuriser · BC04 Optimiser & faire évoluer** (the `Bloc` field on the Retrieva
  board uses these).
- **Separate documentation.** Retrieva has its **own** Docusaurus docs (`retrieva/docs/`), distinct
  from ktayl / `minicloud-platform-docs`. **Certification evidence lives in Retrieva's own docs** at
  `retrieva/docs/docs/certification/` (overview + one page per bloc artefact; raw evidence like the
  RGAA report in `retrieva/docs/static/certification/`). Never put cert artefacts in the
  ktayl/minicloud docs. Artefact index: `certification/overview.md`.
- Memories: [[project_cert1_m1m2_sprint]] (cert = Retrieva), [[project_ktayl_solution_is]] (the IS).

## Portfolio structure — one Project per PRODUCT (since 2026-09-07)

**This supersedes the earlier "two Projects / 2-tier" model.** A single catch-all backlog
(old Project #1) is too vague — it lumps many distinct products together and the fog just moves
down a level. The structure is a **portfolio of products**:

- **One GitHub Project (v2) per _product_.** A **product** = a thing with its own backlog and
  lifecycle; it can span **1..N repos** (e.g. Retrieva = `retrieva` + `retrieva-backend`). Each
  product gets its own board **and** its own BMAD home (see `bmad.md`).
- **Initiative is a _field_, not a board.** The three initiatives — **Insurance LOB**,
  **Certification**, **IS Foundations** — are a grouping dimension on the roll-up (and a label),
  used to slice the PMO view. They are never themselves a board.
- **Project #1 = the roll-up / PMO view only.** It auto-adds every issue from every repo and exists
  to answer "what's in flight across the whole DSI," grouped **Initiative → Product**. It is **not**
  a working backlog — never groom or sprint-plan on #1; do that on the product board.
- **An issue lives in its repo, shows on its product board, and also rolls up to #1.** GitHub lets
  one issue sit on multiple Projects — auto-add workflows place it; you never file it twice.

### The discipline that keeps this a portfolio, not 26-board sprawl
1. **A Project = a product, never a bare repo.** Non-product infra repos attach to a product board
   (e.g. `minicloud-gitops` → the *minicloud Platform* product), they do **not** each get a board.
   Per-*repo* boards are the anti-pattern; per-*product* boards (a product = 1..N repos) are correct.
2. **Create a board when the product has real work** — don't pre-create empty boards for
   `claims`/`portal` before they exist. Promote a sub-product to its own board when it earns it
   (multi-repo, own sprint cadence, own stakeholders) — exactly how Retrieva graduated out of
   "Certification".
3. **The roll-up (#1) + the Initiative field are what make many boards coherent** — that is precisely
   what the old disconnected-boards anti-pattern lacked.

### Product boards (the live set — extend as products start)

| Initiative | Product board | BMAD home repo | Member repos (auto-add → board + #1) |
|---|---|---|---|
| Certification | **Retrieva — RNCP39583** (#2) | `retrieva` | `retrieva`, `retrieva-backend` |
| Insurance LOB | **ktayl Policy Service** (#6) | `ktayl-policy-service` | `ktayl-policy-service` |
| Insurance LOB | **ktayl Public Web** (#7) | `ktayl-solution-web` | `ktayl-solution-web` |
| Insurance LOB | **ERPNext (HR/Finance)** (#8) | `minicloud-erpnext` | `minicloud-erpnext` |
| Insurance LOB | **ktayl Claims** (#11) | `ktayl-claims` | `ktayl-claims` (FNOL/lifecycle, adjusters, subrogation, fraud/SIU, litigation) |
| Insurance LOB | **ktayl Underwriting & Pricing** (#12) | `ktayl-underwriting` | `ktayl-underwriting` (workbench, guidelines, committee, rating, cat) |
| Insurance LOB | **ktayl Distribution & CRM** (#13) | `ktayl-distribution` | `ktayl-distribution` (broker portal, CRM, DUA/binders, co-insurance, commissions) |
| Insurance LOB | **ktayl Insurance Finance & Billing** (#14) | `ktayl-finance` | `ktayl-finance` (billing, IFRS 17, reserving, reinsurance) |
| Insurance LOB | **ktayl Insurance LOB — Product Lines** (#9) | `ktayl-solution-web` | the actual LOB lines (Marine, Engineering, Financial Lines, Collaborateurs, International, ART) until each graduates |
| Insurance LOB | **Regulatory & Compliance** (#15) | `minicloud-gitops` | GDPR/AML-KYC/PIA/BCP/ACPR (the insurer's regulatory obligations) |
| IS Foundations | **minicloud Platform (IDP)** (#3) | `minicloud-gitops` | `-gitops`, `-ansible`, `-opentofu`, `-backstage`, `-ops`, `platform-demo` |
| IS Foundations | **AI Platform** (#4) | `minicloud-agent` | `-agent`, `-crew-agent`, `-open-webui`, `-plane` |
| IS Foundations | **Data Platform** (#5) | `minicloud-gitops` | (data pipeline / BI work) |
| IS Foundations | **Digital Workplace (M365 Alternative)** (#10) | `ktayl-workplace` | `ktayl-workplace`, `minicloud-onlyoffice` (+ Stalwart/Nextcloud/Matrix/Jitsi/Docuseal/n8n/Authentik/Vaultwarden/Homer/Paperless/Asterisk via `minicloud-gitops`) |
| — (roll-up) | **andrelair Platform Portfolio** (#1) | — | **all** repos, grouped Initiative → Product |

**ktayl-IS split (2026-09-09→10):** the vague "ktayl Insurance LOB" catch-all (#9) was broken into
real products — **Digital Workplace** (#10, first), then **Claims** (#11), **Underwriting & Pricing**
(#12), **Distribution & CRM** (#13), **Insurance Finance & Billing** (#14), and **Regulatory &
Compliance** (#15). ~57 issues were redistributed off #9/#3 to their belonging boards (policy-service
stories → #6, INS-*/OPS-* → their products, workplace/comms tools → #10, compliance → #15); #9 now
holds only the six real **LOB product lines** (Marine/Engineering/Financial-Lines/Collaborateurs/
International/ART) until each earns its own board.

Future products (`portal`, a broker portal, …) get a board **the day their work starts**, with an
`Initiative` value and a BMAD home repo. **Auto-add for a new product's home repo → #1 is UI-only**
(Project #1 → Workflows → Auto-add) — wire it when the repo is created; until then add its issues to
#1 by hand + set `Initiative`. **Known polish debt:** boards #3–#9 predate the Priority field
(created via `gh project create`) — add a Priority single-select to each when next grooming.

### Where does a new issue go? (decision rule)
- Identify the **product** it belongs to → it goes on **that product's board**, in the **repo it
  concerns** (frontend story → the frontend repo; backend story → the backend repo).
- If it's genuinely cross-product / programme-level (governance, portfolio ops) → it belongs to the
  **initiative's home product** (e.g. platform-wide governance → *minicloud Platform*), not a new board.
- Every issue also auto-adds to **#1** (the roll-up). You never add to #1 by hand.

**Not backlog — do not surface on any board:** `minicloud-gitops` `[CHANGE]` issues labelled
`change-record` (~290) are the automated ITIL/DORA **change-management audit log** (one per prod PR),
not roadmap work. Exclude `label:change-record` from board views. Only real `enhancement`/`bug`
issues from gitops belong on the *minicloud Platform* board.

**BMAD ties in per product** — each product's stories live in its **home repo** under `bmad/stories/`
and sync to issues via the org-shared reusable workflow, routed to the member repo + product board by
frontmatter `repo:` / `project:`. See `bmad.md` (*Per-product BMAD*).

## Mandatory rules when working on any issue

### 1. Link every PR to its issue

When opening a PR that implements (or partially implements) an issue, include the link in the PR body:

```
Closes andrelair-platform/<repo>#<NUMBER>
```

or for partial work:

```
Relates to andrelair-platform/<repo>#<NUMBER>
```

GitHub Projects picks up the linked PR automatically and shows it in the "Linked pull requests" column.

### 2. Create sub-issues for large issues

If an issue is too large to close in a single PR (epics, multi-week work), break it into sub-issues in
the **same repo**, then link them via GitHub's native sub-issues feature (Projects v2) — the
"Sub-issues progress" field on the board auto-populates.

```bash
gh issue create \
  --repo andrelair-platform/<repo> \
  --title "[<id>] Sub-task title" \
  --label "<same labels as parent>" \
  --body "Parent: andrelair-platform/<repo>#<PARENT_NUMBER>\n\n..."
```

### 3. Update issue status on the product board as you work

Use the board `Status` field — update it as work progresses. Status flow mirrors Scrum:
`Backlog → This Sprint → In Progress → Blocked → In Review → Done`. The GraphQL field/option IDs
below are for **Project #1**; each product board has its own IDs (query them per board with
`gh project field-list <n> --owner andrelair-platform`).

```bash
# Project #1 Status field ID: PVTSSF_lADOEN4i9s4BbQIFzhWB8R4
# Option IDs: Backlog 3ac5aad0 · This Sprint 26e76715 · In Progress d4b08afe
#             Blocked 9ab1df6d · In Review b6090f99 · Done 99316423
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwDOEN4i9s4BbQIF"
    itemId: "<ITEM_ID>"
    fieldId: "PVTSSF_lADOEN4i9s4BbQIFzhWB8R4"
    value: { singleSelectOptionId: "d4b08afe" }
  }) { projectV2Item { id } }
}'
```

### 4. Set Priority + Sprint when promoting an issue to active work

Set the board's native `Priority` field (separate from labels) and the `Sprint` iteration when moving
an issue into "This Sprint"/"In Progress" — a story without the `Sprint` value won't show on the
`sprint:@current` views (see `agile-execution.md`).

| Board Priority | Label equivalent |
|---|---|
| P1 — Critical | `P1-blocking` |
| P2 — High | `P2-high-value` |
| P3 — Medium | `P4-platform-polish` |
| P4 — Low | — |
| P5 — Deferred | `P5-supplemental` |

### 5. Groom the product board, monitor the roll-up

Work each **product board** for its own backlog. Use **#1** only as the cross-product PMO glance
(what's in flight, by Initiative → Product). Don't run day-to-day grooming on #1.

## Project #1 field IDs (roll-up, for GraphQL mutations)

| Field | ID |
|---|---|
| Status | `PVTSSF_lADOEN4i9s4BbQIFzhWB8R4` |
| Priority | `PVTSSF_lADOEN4i9s4BbQIFzhWB9gE` |
| Domain | `PVTSSF_lADOEN4i9s4BbQIFzhXy6tY` |
| Effort | `PVTSSF_lADOEN4i9s4BbQIFzhXy6v4` |
| Sprint | `PVTIF_lADOEN4i9s4BbQIFzhXy__c` |
| Track | `PVTSSF_lADOEN4i9s4BbQIFzhaH6GY` |
| Kind | `PVTSSF_lADOEN4i9s4BbQIFzhaLrh8` |
| Start Date | `PVTF_lADOEN4i9s4BbQIFzhaLriA` |
| Project node ID | `PVT_kwDOEN4i9s4BbQIF` |
