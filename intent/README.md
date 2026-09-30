# intent/ — lightweight idea capture (AI-native SDLC Play 1)

The **front door** for work that isn't yet a story. Anyone (engineer or not) brainstorms
an idea with Claude and commits a **proto-spec** here in their own words — no backlog
ceremony, no hand-off. The product owner picks it up and it flows into design.

## The lightweight artifact chain

```
intent/<slug>.md   →   spec / architecture   →   plan.md (per change)   →   PR (diff + tests)
   (Play 1)              (BMAD / Play 2)          (Play 3)                  (Play 10 review)
```

Each stage **commits a validated artifact** and the next stage reads it — that chain is
also the audit trail (who asked for what, what was decided, who approved). This `intent/`
folder is the cheap entry; heavier products still run the full BMAD chain (`bmad/`,
`.claude/rules/bmad-compliance.md`) — intent just removes the "convince someone to write
it up" step at the start.

## How to file an intent
1. Brainstorm with Claude (here, claude.ai, or Claude Code) until the idea is concrete.
2. `/capture-intent "<one line>"` drafts `intent/<slug>.md` from `TEMPLATE.md`, or copy the
   template by hand. Fill: Problem / Proposed outcome / Affected users+systems /
   Constraints / Open questions.
3. Correct anything Claude misread, then **commit it** (author + timestamp = the record).
4. The product owner accepts or closes it → it becomes a spec/story (design), or a
   `plan.md` for a small change.

## plan.md (Play 3)
Before implementing a **non-trivial** change, write a short `plan.md` from
`bmad/templates/plan-template.md` (files that change · order · risks · proof) — Claude Code
**plan mode** produces it; commit the approved version so the PR review can check the diff
against it. Update `plan.md` in the same commit if implementation deviates.

## Not a replacement for the tracker
An accepted intent still becomes a GitHub issue on its product board (per
`.claude/rules/github-projects.md`). `intent/` holds the *origin* artifact, not the status.
