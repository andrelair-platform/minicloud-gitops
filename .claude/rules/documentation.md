# Documentation Standard — always document what was built or solved

Every meaningful piece of work — a new capability, a hardening epic, a resolved
incident, a non-obvious fix — must leave a **technical written trace**, not just
a merged PR. Code shows *how*; docs explain *what*, *why*, and *how to operate/
audit it*. This is what makes the platform defensible in an architecture review,
a DORA/AI-Act audit, or a job interview.

## The rule

**When you finish a workstream, update the docs in the same effort.** Do not
consider a story/epic/incident "done" until its documentation reflects reality.

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

## What a good technical doc contains

1. **What was done** — the capability/fix in one paragraph.
2. **Why** — the problem or driver (incident, compliance, gap).
3. **Architecture / how it works** — a diagram or table; the real components.
4. **What was delivered** — a story/change table with concrete outcomes.
5. **How to operate / verify / audit it** — commands, endpoints, checks.
6. **Compliance mapping** where relevant (AI-Act/DORA/GDPR/ACPR).
7. **Status honesty** — if a doc has superseded sections, say so with a `:::note`
   rather than leaving stale info unmarked.

## Discipline

- **Supersede, don't lie:** when reality diverges from an old doc, add a status
  note and a current section — don't silently leave outdated content.
- **Build-check before merge:** `npm run build` on the docs site fails on broken
  internal links — always run it (validates `en` + `fr`).
- **Branch-protected repos:** docs repos main is protected → land via PR.
- **Link, don't duplicate:** the overview page points to the detailed in-repo docs.

## Reference implementation

`docs/ai-ml/12-ai-gateway.md` (minicloud-platform-docs) — the *AI Gateway
Enterprise Hardening* section: what/why/architecture diagram + a 13-story
delivery table + cost model + compliance mapping + pointers to the detailed
governance docs (`model-governance-matrix.md`, `dora-audit.md`), with a `:::note`
marking the pre-hardening sections as partially superseded.
