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
- **Product boards are authoritative — there is NO roll-up board.** The old aggregator Project **#1
  was deleted (2026-09-10)** as redundant: it duplicated every issue into a flat, unnavigable list
  and added maintenance with little value. The **product boards (#2–#17) are the source of truth**;
  each issue lives in its repo and on exactly its product board(s).
- **Initiative is a grouping concept (a label / per-board field), not a board.** The three
  initiatives — **Insurance LOB**, **Certification**, **IS Foundations** — group products; use a
  label or a per-board field if you need to slice by them. They are never themselves a board, and
  there is no longer a single project that groups by them.
- **Cross-product glance without a roll-up:** use GitHub's org-level issue search / saved filters
  (e.g. `org:andrelair-platform is:issue is:open label:P1-blocking`) instead of a duplicate board.
  If a roll-up is ever wanted again, recreate it with auto-add workflows — don't hand-maintain one.

### The discipline that keeps this a portfolio, not 26-board sprawl
1. **A Project = a product, never a bare repo.** Non-product infra repos attach to a product board
   (e.g. `minicloud-ansible` → the *GitOps — Platform Engineering* product), they do **not** each get
   a board. Per-*repo* boards are the anti-pattern; per-*product* boards (a product = 1..N repos) are correct.
2. **Create a board when the product has real work** — don't pre-create empty boards for
   `portal` before it exists. Promote a sub-product to its own board when it earns it
   (multi-repo, own sprint cadence, own stakeholders) — exactly how Retrieva graduated out of
   "Certification" and the LOB products split out of the "Insurance LOB" catch-all.
3. **Each product board is self-contained** (own backlog + BMAD home) — that, plus the per-product
   BMAD sync, is what keeps many boards coherent without a central roll-up.

### Product boards (the live set — extend as products start)

| Initiative | Product board | BMAD home repo | Member repos / scope |
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
| Insurance LOB | **Regulatory & Compliance** (#15) | `ktayl-compliance` | GDPR/AML-KYC/PIA/BCP/ACPR (the insurer's regulatory obligations) |
| IS Foundations | **GitOps — Platform Engineering** (#3) | `minicloud-gitops` | `-gitops`, `-ansible`, `-opentofu`, `-backstage`, `-ops`, `platform-demo` |
| IS Foundations | **AI Platform** (#4) | `minicloud-agent` | `-agent`, `-crew-agent`, `-open-webui`, `-plane` |
| IS Foundations | **Data Platform** (#5) | `minicloud-gitops` | (data pipeline / BI work) |
| IS Foundations | **Digital Workplace (M365 Alternative)** (#10) | `ktayl-workplace` | `ktayl-workplace`, `minicloud-onlyoffice` (+ Stalwart/Nextcloud/Matrix/Jitsi/Docuseal/n8n/Authentik/Vaultwarden/Homer/Paperless/Asterisk via `minicloud-gitops`) |
| IS Foundations | **ktayl ITSM (GLPI)** (#16) | `ktayl-itsm` | `ktayl-itsm` (GLPI ITIL v4, CMDB, SLA/KPI, helpdesk) |
| IS Foundations | **Access Governance (IAM/IGA)** (#17) | `ktayl-iam` | `ktayl-iam` (MidPoint IGA, role/entitlement, certification, PAM, SCIM, SoD) |

**ktayl-IS split (2026-09-09→10):** the vague "ktayl Insurance LOB" catch-all (#9) was broken into
real products — **Digital Workplace** (#10), **Claims** (#11), **Underwriting & Pricing** (#12),
**Distribution & CRM** (#13), **Insurance Finance & Billing** (#14), **Regulatory & Compliance**
(#15), **ktayl ITSM (GLPI)** (#16), **Access Governance (IAM/IGA)** (#17). All backlog issues were
redistributed to their belonging boards; #9 now holds only the six real **LOB product lines**
(Marine/Engineering/Financial-Lines/Collaborateurs/International/ART) until each earns its own board.
The old aggregator **Project #1 was then deleted (2026-09-10)** once every issue had a product-board
home — the product boards are the source of truth; there is no roll-up.

Future products (`portal`, a broker portal, …) get a board **the day their work starts** with a BMAD
home repo. **Known polish debt:** issues that landed on boards #3–#9 (which pre-dated the Priority
field) may not have a Priority set yet — populate on next grooming.

### Where does a new issue go? (decision rule)
- Identify the **product** it belongs to → it goes on **that product's board**, in the **repo it
  concerns** (frontend story → the frontend repo; backend story → the backend repo).
- If it's genuinely cross-product / programme-level (governance, portfolio ops) → it belongs to the
  **initiative's home product** (e.g. platform-wide governance → *GitOps — Platform Engineering*), not a new board.
- There is **no roll-up** to add to — an issue's board membership is complete once it's on its product board.

**Not backlog — do not surface on any board:** `minicloud-gitops` `[CHANGE]` issues labelled
`change-record` are the automated ITIL/DORA **change-management audit log** (one per prod PR), not
roadmap work — exclude `label:change-record` from board views. Automated **CSPM `IAM Audit` / cloud
security-scan findings** (`🔴 …[IAM_OVERPERMISSIVE]` etc.) are likewise scanner output, not roadmap.
Only real `enhancement`/`bug` issues from gitops belong on the *GitOps — Platform Engineering* board.

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
`Backlog → This Sprint → In Progress → Blocked → In Review → Done`. **Each product board has its own
field + option IDs** — query them per board (there is no shared roll-up any more):

```bash
# discover a board's Status field id + option ids
gh project field-list <board-number> --owner andrelair-platform --format json \
  | python3 -c "import sys,json;[print(f['id'],f['name'],[o['name'] for o in f.get('options',[])]) for f in json.load(sys.stdin)['fields'] if f['name']=='Status']"
# board node id
gh project view <board-number> --owner andrelair-platform --format json --jq .id
# then set it
gh project item-edit --id <ITEM_ID> --project-id <BOARD_NODE_ID> \
  --field-id <STATUS_FIELD_ID> --single-select-option-id <OPTION_ID>
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

### 5. Groom each product board directly

Work each **product board** for its own backlog. There is no roll-up to monitor — for a cross-product
glance use org-level issue search (e.g. `org:andrelair-platform is:issue is:open label:P1-blocking`).

## Board field IDs

There is **no shared roll-up board**; each product board carries its own field + option IDs. Query
them per board as needed:

```bash
gh project view <n> --owner andrelair-platform --format json --jq .id          # board node id
gh project field-list <n> --owner andrelair-platform --format json             # fields + option ids
```

Every product board (#2–#17) has a **Priority** single-select (`P1 — Critical … P5 — Deferred`) and
the default **Status** field; boards created via the API were given Priority explicitly (2026-09-10).
