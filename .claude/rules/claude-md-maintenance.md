# CLAUDE.md — thin stable pointer (rolling-window RETIRED 2026-10-25)

`CLAUDE.md` is a **thin, stable entry point**: architecture/quick-access, the two-layer model, and
pointers to where knowledge actually lives. It is **not** a session log.

## The rule
- **CLAUDE.md holds only stable, slow-changing orientation** — the architecture table, the two-layer
  model, quick-access commands, and the knowledge-map pointers. Edit it rarely (only when that stable
  content genuinely changes).
- **Session facts go to their real home, never into CLAUDE.md:**
  - *what shipped* → **git history / merged PRs / closed issues** (the real, auditable trail)
  - *reusable facts & gotchas* → the **memory system** (`memory/*.md`, index `MEMORY.md`; selective recall)
  - *stable conventions / runbooks* → **`.claude/rules/*.md`** (constraints) + **skills** (procedures)
  - *current operational state* → derive live (`minicloud-recovery-check`); controller CLAUDE.md for ops specifics
- **No per-session "session blocks." No `CLAUDE-history.md` rolling archive. No two-file sync chore.**

## What this REPLACES (revoked)
The old **rolling-window** model (last-2-session-blocks + migrate-oldest-to `CLAUDE-history.md` +
end-of-session two-file sync) and the **"CLAUDE.md Sync Rule — MANDATORY"** are **revoked** — they
duplicated what git/issues/memory already hold, added per-session toil, and fought the `guard-write`
hook (which correctly refuses CLAUDE.md edits). Rationale matches `bmad-compliance.md`: *the code/git IS
the context; restating it gives no gain and real cost.* Historical session blocks already in a CLAUDE.md
may be left as-is or trimmed opportunistically; do not add new ones.
