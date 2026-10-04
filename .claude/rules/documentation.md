# Documentation Standard — always document what was built or solved

Every meaningful piece of work — a new capability, a hardening epic, a resolved
incident, a non-obvious fix — must leave a **technical written trace**, not just
a merged PR. Code shows *how*; docs explain *what*, *why*, and *how to operate/
audit it*. This is what makes the platform defensible in an architecture review,
a DORA/AI-Act audit, or a job interview.

## The rule

**When you finish a workstream, update the docs in the same effort.** Do not
consider a story/epic/incident "done" until its documentation reflects reality.

## Documentation is a Definition-of-Done GATE — MANDATORY, not a follow-up

**Every project / epic / feature / third-party deployment is NOT "Done" until its documentation is
updated in the same effort** — at minimum its **org-site map page** (`minicloud-platform-docs`) brought
to **as-built** (what's live · how to operate/verify · decisions resolved), plus any ADR/runbook the
scope warrants. This is a **blocking DoD item at the same tier as tests and the QA gate** — the doc PR
lands **with** (or immediately after) the deploy PR, build-checked (`npm run build`). "I'll document it
later" or **waiting to be asked is the failure mode this rule forbids.**

> **Anti-pattern actually observed (2026-10-03, BookStack #10 + GLPI #16):** the build was finished and
> marked done, but the org-site doc was only written when the owner later asked. Shipping a capability
> without its as-built doc leaves the platform undefensible in an audit/interview and rots the map.
> For a **new product** this is Path-C `project-governance.md` work; for **any** deploy it's a DoD gate.

**Enforcement:** the Definition of Done (`agile-execution.md` §2) and the BMAD gates
(`bmad-compliance.md`) both carry "org-site as-built doc updated + build-checked" — a story/epic that
deployed something cannot be closed without it. When you finish building, the **next action is the doc**,
not the next feature.

## Where documentation lives (pick by scope)

| What | Where | When |
|---|---|---|
| **Service/feature overview** (the "map") | org-wide Docusaurus **`minicloud-platform-docs`** — one page per service under `docs/<section>/` | new service, or a capability that changes what a service does |
| **Detailed design / governance / runbooks** | in the owning repo (`<repo>/docs/` or `<repo>/website/`) | data models, ADRs, compliance matrices, audit procedures |
| **Reusable gotcha / fact** | the memory system (`MEMORY.md` index) | a non-obvious lesson worth recalling later |
| **Current state + last 2 sessions** | `CLAUDE.md` (see `claude-md-maintenance.md`) | every session |
| **Stable convention / runbook** | `.claude/rules/*.md` | a durable rule |

The org-wide docs site is a **map, not a library** — summary + pointers to the
detailed docs that live with the code (see `conventions.md`).

**Mandatory pairing — a repo ADR is not "done" without its org-site map entry.** An ADR / detailed
design in `<repo>/docs/` (e.g. `minicloud-gitops/docs/*.md`) MUST be paired with an **overview + pointer
page on the org Docusaurus** (`developer-platform/<slug>` or the relevant section) that summarises it and
links to the ADR's **GitHub blob URL**. The ADR is the source of truth (versioned + CODEOWNERS-gated with
the code); the org-site page is how it's discovered. Do **not** move the ADR onto Docusaurus, and do
**not** leave it without a pointer. Reference pattern: `developer-platform/delivery-workflow` →
`docs/helm-golden-path.md`; `developer-platform/dns-naming-externaldns` → `docs/dns-naming-and-externaldns.md`.

## What a good technical doc contains

1. **What was done** — the capability/fix in one paragraph.
2. **Why** — the problem or driver (incident, compliance, gap).
3. **Architecture / how it works** — a diagram or table; the real components.
4. **What was delivered** — a story/change table with concrete outcomes.
5. **How to operate / verify / audit it** — commands, endpoints, checks.
6. **Compliance mapping** where relevant (AI-Act/DORA/GDPR/ACPR).
7. **Status honesty** — if a doc has superseded sections, say so with a `:::note`
   rather than leaving stale info unmarked.

## Verified reality — write what you actually ran, not what you assume (AI era)

The value of a doc is no longer technically-correct prose (AI generates that in seconds) — it's
helping a reader get from *"I don't understand this"* to *"I can implement this."* Three hard rules:

1. **Every command / endpoint / output in a doc was actually RUN against the live system — not
   assumed.** The flow is `understand → build → test → document → review`, never
   `prompt → answer → publish`. An "Operate / verify" block shows the real command *and its real
   result* (the `http=200 ssl_verify=0`, the `Synced/Healthy`, the actual `401`) because you ran it.
   If you didn't run it, it doesn't go in the doc.
2. **Verification is the non-delegable skill — not prompt-writing.** When AI drafts a doc, verify
   every claim against the running system before it ships (does that package / flag / endpoint exist
   and return what the doc says?). Ref: this is the docs-specific face of `ai-native-engineering.md`.
3. **The reader test (before merging a doc):** hand it to someone who doesn't know the system — can
   they, in order, (a) say what it is, (b) operate/verify it, (c) act on it, without asking you? A doc
   only its author can use isn't done. Follow the system's real shape ("documentation follows the
   architecture; it doesn't fight it"), and pick the right *type* — an as-built map page, a runbook, an
   ADR and a tutorial are different artefacts; don't conflate them.

**API / endpoint docs — answer the reader's immediate questions before they ask.** An endpoint line
like `POST /api/users` is not documented by "creates a user." Cover, every time: **auth** (who may call
it), **headers**, **request body** + **required fields**, **validation errors**, **response shape**,
**status codes**, and **idempotency** (safe to retry?). A reader hits these nine questions the moment
they try to call it — a good doc has already answered them. (Applies to our service docs: ktayl-iam,
ktayl-policy-service, underwriting, …)

## Discipline

- **Supersede, don't lie:** when reality diverges from an old doc, add a status
  note and a current section — don't silently leave outdated content.
- **Build-check before merge:** `npm run build` on the docs site fails on broken
  internal links — always run it (validates `en` + `fr`).
- **Branch-protected repos:** docs repos main is protected → land via PR.
- **Link, don't duplicate — and always link:** the org-site overview points to the detailed in-repo
  doc; never mirror the ADR body onto the org site, and never leave a repo ADR without its org-site
  pointer (the *Mandatory pairing* rule above).

## Reference implementation

`docs/ai-ml/12-ai-gateway.md` (minicloud-platform-docs) — the *AI Gateway
Enterprise Hardening* section: what/why/architecture diagram + a 13-story
delivery table + cost model + compliance mapping + pointers to the detailed
governance docs (`model-governance-matrix.md`, `dora-audit.md`), with a `:::note`
marking the pre-hardening sections as partially superseded.
