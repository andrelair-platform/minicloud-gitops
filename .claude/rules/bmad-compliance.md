# BMAD Compliance — Pre-Implementation Gate

BMAD governs **intent → implementation → review**; the platform owns everything around it (Git,
CI/CD, Kargo, ArgoCD, CODEOWNERS, observability — see `gitops.md`, `testing.md`). The artefact
burden **scales to the size and risk of the work** — do NOT run the full planning lifecycle for a
one-line fix, and never skip it for a new product.

## Delivery paths — choose ONE per change (gate artefacts on the PATH, not the repo)

| Path | When | Mandatory artefacts before code | Flow |
|---|---|---|---|
| **A — Small change** | bug, config, small self-contained feature, a platform chore, docs — fits in **one session**, no new architecture | **none** (the `.claude/rules/*` constitution is always in force) | branch → implement (`/bmad-build` optional) → tests → PR → CI + CODEOWNERS |
| **B — Feature / Epic** | a feature spanning several stories, a new service on an **existing** product, a non-trivial integration | a **spec/epic + stories** (+ readiness gate for the sprint); PRD/architecture only if the design is new | stories → `/bmad-sprint-planning` (PASS) → `/bmad-build` per story → review → PRs |
| **C — New product / major initiative** | a new product (own backlog + board), or work likely **> ~20 build sessions** | the **full set** below: `project-context.md` + PRD + architecture + epics + readiness gate | full lifecycle (see *BMAD Workflow*), + the governance gate below |
| **E — Emergency / hotfix** | prod incident, security patch, rollback | **none up front** — fix first; **backfill** a story/issue + a `deferred-work.md` note within 24h | branch → fix → PR (expedited CODEOWNERS) → **retro issue** capturing root cause |

**How to pick:** new product or >20 sessions → **C**. Multi-story / new service on an existing
product → **B**. One-session, no new architecture → **A**. Prod is down → **E**. When unsure between
two, pick the heavier one. **This session's wrapper-chart migration + promotion fixes were Path A/B**
(chores/fixes straight to PR) — that is correct, not a process bypass.

**The Rule (restated):** never write code for **Path B or C** without its mandatory artefacts; for
**Path A/E** the artefacts are not required, but the constitution (`.claude/rules/*`), tests, PR +
CODEOWNERS gate **always** apply. If a "small change" turns out to need architecture, **stop and
promote it to Path B**.

## The pre-code artefact chain (the full standard — scale by path)

Each artefact removes a **different kind of ambiguity**, in order: Brief = *business* → PRD =
*product/requirements* → UX = *interaction* → Architecture = *technical* → SPEC = *epic* → Story =
*implementation scope* → Readiness = *cross-document inconsistency* → Build = code. Produce them
**top-to-bottom** (architecture precedes story breakdown, because design shapes decomposition).

**Applicability gates on the delivery path** (A/E produce none; B = a subset; C = the full chain).
🔴 mandatory · 🟢 recommended · 🟡 conditional/optional · — n/a.

| # | Artefact (file) | Path B | Path C | Owner (role) | Tool |
|---|---|---|---|---|---|
| 0 | **Context block** `AGENTS.md` (repo-specific, tiny) | 🟢 | 🔴 (once/repo) | DO/Eng | `/bmad-project-context` |
| 1 | Research `research.md` | 🟡 if novel | 🟡 if novel | BA / Product | `/bmad-deep-recon` |
| 1 | **Product Brief** `brief.md` (+`addendum.md`) | 🟡 | 🟢 recommended | PM / PO | `/bmad-product-brief` |
| 1 | *(alt)* PRFAQ `prfaq-<p>.md` | 🟡 | 🟡 optional | PM | `/bmad-prfaq` |
| 2 | **PRD** `prd.md` — the product contract | 🟡 if new design | 🔴 mandatory | PM / PO | `/bmad-prd` |
| 3 | **UX** `DESIGN.md` + `EXPERIENCE.md` | 🟡 if UI | 🔴 **if UI** | UX/UI | `/bmad-ux` |
| 4 | **Architecture** `architecture.md` (spine) | 🟡 if new design | 🔴 mandatory | SA / TL | `/bmad-architecture` |
| 5 | **SPEC per epic** `specs/spec-<x>/SPEC.md` | 🔴 mandatory | 🔴 mandatory | TL / BE | `/bmad-spec` |
| 6 | **Epics + Stories** (ACs, deps, DoD) | 🔴 mandatory | 🔴 mandatory | PM + TL | `/bmad-create-epics-and-stories` |
| 7 | **Readiness gate** verdict (PASS/CONCERNS/FAIL) | 🔴 mandatory | 🔴 mandatory | TL | `/bmad-sprint-planning` |
| 8 | **`sprint-status.yaml`** (engineering status) | 🔴 mandatory | 🔴 mandatory | Eng | `/bmad-sprint-planning` |

Planning artefacts live in `_bmad-output/planning-artifacts/` (specs under `specs/`); stories land in
the product **home repo** `bmad/stories/` and sync to issues (see `bmad.md`). Owners map to the 15
roles in `project-governance.md`; the RACI records who approved each. **BMAD drafts, the owner
approves** — an artefact isn't "done" until its human owner signs off (the governance + readiness gates).

**The SPEC layer (the key scalability move).** The **PRD is product-level** ("what we're building and
why", owned by Product); a **SPEC is a compact per-epic implementation contract** derived from the PRD
+ architecture. Don't feed the whole PRD into every build session — `/bmad-build` works against the
**epic's SPEC**, so each bounded piece (auth, claims, billing…) carries just its own contract:
`specs/spec-claims/SPEC.md` → its stories → build. This keeps context tight and lets several devs/agents
work in parallel without re-deriving the product.

**sprint-status.yaml ≠ the system of record.** It's BMAD's *engineering-side* status view; the
**GitHub Project board is the org tracker** (`github-projects.md`). They coexist — don't duplicate.

## Operating the chain in an organization (disciplines, not just documents)

The chain above is *which* documents exist; these are the rules for *how they behave* once more than
one person must agree, several epics build against the same decisions, or someone signs off before
spend. Planning docs are **contracts between people first**, skill-input second.

**1. Spec-first is the default; the PRD is the exception.** Most work goes **straight to `/bmad-spec`**
from whatever defined the intent (a forged idea, a PRFAQ summary, an issue) → one SPEC per epic. Reach
for a **PRD only** when (a) people who didn't do the thinking must approve *what the product is*, (b)
several epics/teams/agents build against the same decisions and must not diverge, or (c) a
regulator/steering-committee requires named evidence. `/bmad-spec` tells you if the input is too thin
(→ escalate to PRD); until it does, **no PRD is required**. This is Path A/B; the full PRD chain is Path C.

**2. One source of truth — change flows from the source outward.** Each document has **one writer +
one owner**: the PRD says *what the product is* (Product), the spine says *how epics stay compatible*
(Architect/TL), a SPEC says *what one epic does* (its engineer). Reviewers read **copies** and will ask
for a change in whatever doc they're holding — apply it to the doc it **belongs** to (product →
PRD, cross-epic → spine, one-epic → that SPEC), then **re-run the downstream skill to regenerate**.
**Never hand-edit a derived doc** (`prd.md`/`architecture.md`/`SPEC.md`) to patch around an upstream
one — that's how the documents stop agreeing. Editing the source + regenerating keeps them consistent.

**3. Brownfield onboarding — bring the documents you have (our normal case).** Most of our products
already exist (retrieva, ktayl-*, the agents). Don't replace the planning you run — **feed it in**:
- `/bmad-prd` opens with a brain-dump + reads files you point at → run **Validate** for a findings
  report (nothing changed), or **Create/Update** to bring `prd.md` in line with your existing PRD,
  tagging filled gaps `[ASSUMPTION]`. After that the team-edited copy is the source; re-run in
  **Update** mode when it changes — never hand-edit `prd.md` to catch up.
- `/bmad-architecture` on an existing system **reads the live code and records the conventions already
  there**, rather than proposing new ones (it becomes the spine of what *is*).
- Tracker stays the tracker (GitHub Projects); `sprint-status.yaml` is the engineering view, **no auto-sync**.

**4. The five sign-off moments (put existing approvals here — each produces reviewable evidence).**

| Moment | What's judged | Blocks |
|---|---|---|
| PRFAQ / brief verdict | is the concept strong enough to resource? | writing the PRD |
| PRD **validate** | findings report on the PRD, unchanged | design + architecture work |
| **Architecture spine review** (= the *Governance gate* below) | the cross-epic decisions, alternatives weighed | writing epic SPECs |
| **Readiness gate** (`/bmad-sprint-planning`) | could a dev implement these stories without inventing decisions? | generating sprint tracking |
| **Retrospective verdict** (`/bmad-review`) | did the epic meet its own acceptance criteria? | starting the next epic |

In regulated/cert settings these written results **are the audit trail** (map to the RNCP blocs / DORA).

**5. Mid-flight requirement change — same path as the original, from the source out.**
`/bmad-prd` **Update** (surfaces conflicts with earlier decisions before applying) → if it touches a
cross-epic call, update the **spine** → re-run `/bmad-spec` for affected epics (**capability IDs stay
stable**, so unaffected stories stay unaffected) → re-run story-breakdown / `/bmad-sprint-planning`
(finished work stays finished). For a change too big for one story to absorb, run **`/bmad-correct-course`**
first (it produces a sprint change proposal — what changes, what stays, in what order).

**6. Several epics at once — the spine is what makes parallel safe.** One PRD, one spine, one SPEC per
epic; engineers take epics in parallel **only when boundaries are explicit**. An epic's spine
**inherits the parent's decisions** and records only what the parent left open. Run **integration
checks + a retrospective at *every* epic boundary**, not only at the end.

## Existing-codebase context — the code is primary; the context block is tiny

**Almost all our work is brownfield** (retrieva, ktayl-*, the agents, the platform itself). The rule
there is the opposite of "write everything down": **the source IS the context.** Agents read code
better than prose about code — feeding them textual descriptions of what they can already read creates
contradiction, context-bloat, and staleness (measured: restating the repo gives **no success gain and
+20% inference cost**). So:

- **Code is read live, never stored.** Repo overviews, directory trees, stack lists, architecture
  *summaries* do **not** go in a context file — they rot on every commit and the agent derives them
  in seconds. (This is why the old `bmad-document-project` / `bmad-generate-project-context` skills are
  **deprecated** → both forward to `bmad-project-context`.)
- **The implementation-context block is tiny and evidence-based** — it holds only what the code
  *cannot* cheaply say: **policy** (frozen paths, generated files, branch rules, security/compliance),
  the **command-with-a-catch** (the right command when several look plausible; "suite needs a service
  up first"), **conventions that differ from ecosystem defaults**, **observed pitfalls** (a mistake
  actually seen, not a scan guess), **cross-component rules + required versions**, and **pointers**.
  Test: *would removing this line change agent behaviour?* If not, it doesn't earn a line.
- **Where it lives:** BMAD's standard is a verified block in **`AGENTS.md`** at the repo root (written
  by `/bmad-project-context`, tool-specific imports like `CLAUDE.md` → `@AGENTS.md`). On **our**
  platform the org-level equivalent already exists and is correct: the auto-loaded **`.claude/rules/*.md`**
  ARE the "earns-a-line" layer (policy, non-default conventions, cross-component rules), and
  `claude-md-maintenance.md` already forbids storing code structure/history in `CLAUDE.md`. A per-repo
  `project-context.md`/`AGENTS.md` adds only the **repo-specific** tiny block on top — not a stack/overview doc.
- **Maintain it:** `bmad-project-context` has setup/adopt/**refresh**/**record**/**audit** intents. A
  pitfall goes in only **after** a mistake is seen; audit ends the block **smaller or equal, never larger**;
  a working rule stays until what it's about is gone ("nothing broke lately" is never grounds to delete).

**Two kinds of context, two artefacts (don't merge them):**
- **Implementation context** — constraints/commands/conventions/pitfalls → the tiny `AGENTS.md`/rules
  block (checkable against code, loaded every session, so it must stay small).
- **Planning context** — PRD, rationale, rejected approaches, domain meaning → **archived**, consulted
  in bursts, and kept **out of reach of an ordinary change** (a small Build shouldn't even find the
  greenfield PRD by accident; code can recover behaviour but not intent/rationale).

**Existing-codebase change flow:** small → `/bmad-build` directly (it investigates the repo, records
what to reuse/not-change, asks only if intent is unsettled); several sessions → `/bmad-spec` → a Build
per piece → `/bmad-retrospective`; bigger → a project (Path C). `/bmad-architecture` on an existing
system **reads the live code and records the conventions already there**, not new ones. To break a
pattern, say so in the request **and** record why in the spec — otherwise Build matches the code.

### Mandatory sections (don't leave NFR / security / compliance to memory)

BMAD's default PRD/architecture cover the **functional** product (requirements, journeys, stack,
data model). A regulated insurance IS needs more **before code** — so a **Path C** PRD + architecture
MUST also contain these sections (the readiness gate checks for them; an empty/"N/A" section is a
deliberate, recorded choice, not an omission):

**PRD (`prd.md`) must include:**
- **Non-functional requirements** — SLOs (latency/availability), throughput/scale, data volume/retention.
- **Security requirements** — authn/authz model, data classes handled (P0–P3, see the AI Model
  Governance Matrix), PII/secret handling, the trust/egress boundary.
- **Compliance mapping** — which of DORA / EU AI Act / GDPR / ACPR apply and how (for AI products,
  reuse the `ai-governance` matrix + DORA-audit pattern; cert products map to the RNCP blocs).
- **KPIs / success metrics** + **acceptance criteria** at the product level.
- **Cost / capacity** — the expected footprint, stated before code (this is a resource-constrained
  5-node cluster with tight per-namespace quotas + hard cloud budgets):
  - **cluster footprint** — CPU/mem requests+limits, replica counts, PVC sizes → fits which namespace
    ResourceQuota? (`manifests/quotas/`);
  - **LLM/token cost** — if it calls the AI gateway: tier (on-cluster free / EU paid / US), rough
    tokens/month, the LiteLLM team + budget;
  - **cloud cost** — any cloud resource vs the **€10/mo/provider** cap + the `cloud-adoption.md` gate;
  - **storage/egress growth** — Longhorn PVC growth, backup footprint, external egress.

**Architecture (`architecture.md`) must include:**
- **System boundaries + APIs** (public surface, cross-service contracts).
- **Data model + migration strategy**; where state lives; backup/DR stance.
- **AuthN/AuthZ + secrets** (ESO→Vault; never custom password auth — see `project-context.md`).
- **NetworkPolicy / egress** posture (default-deny + explicit allows — the governed-egress pattern).
- **Observability** — metrics/logs/traces the service exposes (+ LLMOps tracing if it calls an LLM,
  see `llmops.md`); **deployment** = the GAP wrapper-chart golden path (`gitops.md`), never bespoke.
- **Failure modes + rollback** (what happens when a dep is down; how a bad release reverts).

These are **not** produced automatically by running the BMAD step — prompt for them, and the
**governance gate** (architecture + security review) + the readiness gate verify they're present and
sane. The surrounding org standards still own the rest: RACI (`project-governance.md`), test plan
L0–L4 (`testing.md`), runbooks (`gitops.md`/`ops-runbooks`).

## Required Artefacts (per sprint, in minicloud-gitops)

| Artefact | Location | Generated by |
|---|---|---|
| Sprint manifest | `bmad/stories/<project>/<milestone>/SPRINT-OVERVIEW.md` | Backstage scaffolder or manual |
| Story files with YAML frontmatter | `bmad/stories/<project>/<milestone>/S*.md` | Backstage scaffolder or `bmad-to-github.sh` |

## Pre-Flight Check (Path B/C implementation tasks only — Path A/E skip this)

```bash
# In the service repo:
ls AGENTS.md    # (or docs/project-context.md) — the tiny repo context block
ls _bmad-output/planning-artifacts/{prd,architecture,epics,sprint-status}.{md,yaml}
ls _bmad-output/planning-artifacts/specs/*/SPEC.md   # SPEC per epic (mandatory B+C)
# If the product has a UI: ls _bmad-output/planning-artifacts/{DESIGN,EXPERIENCE}.md

# In minicloud-gitops:
ls bmad/stories/<project>/<milestone>/SPRINT-OVERVIEW.md
```

If any **Path-required** file is missing → STOP. Generate the missing artefact first:

| Missing | Command |
|---|---|
| BMAD not installed | `npx bmad-method install --directory . --modules bmm --tools claude-code --yes` |
| context block (`AGENTS.md`) | `/bmad-project-context` → a **tiny** verified block: policy, command-catches, non-default conventions, observed pitfalls, cross-component rules+versions, pointers. **NOT** stack/structure/overview (derivable → hurts). |
| Product Brief | `/bmad-product-brief` |
| PRD | `/bmad-agent-pm` → menu option PRD (or `/bmad-prd`) |
| UX (if UI) | `/bmad-ux` → `DESIGN.md` + `EXPERIENCE.md` |
| Architecture | `/bmad-agent-architect` → menu option architecture (or `/bmad-architecture`) |
| SPEC per epic | `/bmad-spec` → `specs/spec-<x>/SPEC.md` |
| Epics | `/bmad-agent-pm` → menu option CE (Create Epics) |
| Sprint gate | `/bmad-sprint-planning` |
| `SPRINT-OVERVIEW.md` | Copy template from `bmad/templates/SPRINT-OVERVIEW.md` and adapt |

## Story Status Lifecycle (enforce on every PR)

```
Draft      → story being written, not ready to implement
Ready      → story approved, ACs finalized, waiting for sprint slot
In Progress → implementation started, branch open
Done       → PR merged to main (deployed to dev), all ACs checked off
```

**Rules:**
1. Before opening a feature branch: set `status: In Progress` in the story `.md` file
2. On PR merge to main: set `status: Done`, check off all `- [ ] AC-N:` items in the story file
3. Update `SPRINT-OVERVIEW.md` tracker table on both state changes
4. Commit the story status update in the same PR as the implementation (not a separate PR)

## BMAD Workflow (correct order — the full Path C chain; B runs the subset)

```
0. /bmad-forge-idea / /bmad-deep-recon  → (optional) pressure-test + cited research.md
1. /bmad-product-brief                  → brief.md (recommended)
2. /bmad-prd (or /bmad-agent-pm)        → prd.md — the PRODUCT contract (+ NFR/security/compliance/cost)
3. /bmad-ux              (if UI)         → DESIGN.md + EXPERIENCE.md
4. /bmad-architecture (or -agent-architect) → architecture.md — the technical spine
   ── governance gate: architecture + security review (Path C / boundary change) ──
5. /bmad-spec            (per epic)      → specs/spec-<x>/SPEC.md — the per-epic impl contract
6. /bmad-create-epics-and-stories        → epics + stories (ACs, deps, DoD)
7. /bmad-sprint-planning                 → readiness gate → sprint-status.yaml (PASS required)
   ↓
8. /bmad-build <story-id>                → per story, against its SPEC: clarify → implement → review → report
   OR /bmad-build-auto                   → autonomous multi-story loop
   → /bmad-code-review (fresh context) → human PR review (CODEOWNERS + CI)
9. /bmad-review                          → post-sprint retrospective
```

Architecture (step 4) precedes SPEC + story breakdown — design shapes decomposition. Step 7 must
output **PASS** before step 8; CONCERNS requires resolving/accepting the risk first. **Path A/E** skip
steps 0–7 entirely (straight to a scoped build + PR). **Path B** runs the subset its work needs
(typically 5–8, + 2/4 only when the design is new).

## Implementation loop — `/bmad-build` as a full work unit (Path A build-step and Path B/C stories)

`/bmad-build` is not "write code" — it's a bounded engineering unit: **clarify → investigate repo →
plan → human checkpoint → implement → test → self-review → record**. Use it per story (Path B/C) or
for a non-trivial Path-A change; trivial edits may be done directly. Two disciplines make it safe:

- **Scope control → `deferred-work.md`.** Problems discovered mid-change that are *outside the
  current intent* are **recorded, not fixed inline** — appended to `deferred-work.md` (or a follow-up
  issue), never an in-flight detour. This is the hard guard against "while fixing X, refactored half
  the platform." If a discovery *blocks* the change, stop and re-scope (promote Path A → B).
- **Implementation record.** Significant work ends with the No-Black-Box debrief (`ai-native-engineering.md`):
  WHAT / WHY / SHAPE / FAILURE / CHALLENGE / REBUILD? — a comprehension trace, not just a diff.

### Review layers (defence in depth — scale to path)

| Layer | What | Path A | Path B | Path C |
|---|---|---|---|---|
| 1 — self-review | `/bmad-build`'s own review step + tests (`testing.md` L0–L4) | ✅ | ✅ | ✅ |
| 2 — AI independent review | `/bmad-code-review` in a **fresh context** (no memory of writing it) — catches what the author's context is blind to | optional | **recommended** | **required** |
| 3 — human PR review | CODEOWNERS on the gated paths (`gitops.md`) + CI (Checkov/kubeconform/SAST) | ✅ | ✅ | ✅ |
| walkthrough | `/bmad-walkthrough` — by design concern, flags high-risk areas (auth/schema/public API/security) | — | for risky diffs | **for auth/data/security diffs** |

The AI independent pass (layer 2) is distinct from the build's self-review: run it **before** the
human PR review so the human reviews an already-vetted change, not a first draft.

## Governance gate (Path C, and any change touching a security/architecture boundary)

Before a Path-C epic enters build — and for **any** change that crosses a **security or architecture
boundary** regardless of path (authn/authz, data model/migrations, network policy, secrets/Vault,
public API surface, cross-service contracts, IAM, registry/supply-chain) — a **named gate** must be
cleared, not just implied by CODEOWNERS:

1. **Architecture review** — the Tech Lead/Architect (`project-governance.md` role **SA/TL**) signs
   off the design (ADR in `<repo>/docs/` or the org site). `/bmad-party-mode` / `/bmad-agent-winston`
   may produce it; a human approves it.
2. **Security review** — the Security Engineer role (**SEC**) reviews the threat surface for
   boundary-crossing changes (PII flow, egress/NetworkPolicy, secret handling, authz model).
3. **Record it** — the gate decision lands in the epic/ADR and the RACI (`project-governance.md`),
   so "who approved this boundary" is auditable. The CODEOWNERS merge gate is the *enforcement*; this
   is the *decision* that precedes it.

This is the write-up's "governance above BMAD": BMAD proposes the design, **humans own the
architecture/security call**, and the platform (CI + CODEOWNERS + Kargo) enforces it. Routine Path-A
work that touches no boundary needs only the standard CODEOWNERS review.

## New Repo Checklist (BMAD addition)

In addition to the conventions.md repo standardization checklist, every new custom-built repo must:

- [ ] Run `npx bmad-method install --directory . --modules bmm --tools claude-code --yes`
- [ ] Add `_bmad/`, `_bmad-output/`, `.claude/` to `.gitignore`
- [ ] Run `/bmad-project-context` → a **tiny** `AGENTS.md` block (policy/command-catches/non-default conventions/observed pitfalls/cross-component rules — NOT stack/structure/overview); `.claude/rules/*` already carry the org-level layer
- [ ] For **Path B/C** work: complete the planning steps above BEFORE writing story code (Path A/E exempt)
- [ ] Add SPRINT-OVERVIEW.md to the relevant sprint directory in minicloud-gitops

## Applied Repos (track compliance)

| Repo | BMAD Installed | project-context.md | PRD | Architecture | Epics | Sprint Gate |
|---|---|---|---|---|---|---|
| ktayl-policy-service | ✅ 2026-08-16 | ✅ | ✅ (local) | ✅ (local) | ✅ (local) | ✅ 2026-08-16 PASS |
| minicloud-plane | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| platform-demo | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| minicloud-agent | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| minicloud-crew-agent | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
