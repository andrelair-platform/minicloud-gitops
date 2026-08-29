# CLAUDE.md Maintenance — keep it lean (rolling window + memory-first)

`CLAUDE.md` is loaded into context **every session**, so it must stay a **curated snapshot**, not an append-only changelog. Without discipline it bloats (it hit ~7k words / 215 lines before the 2026-08-29 compaction). This rule keeps it bounded.

## The 4-tier knowledge model — put things in the right place

| Tier | Home | Loaded? | Holds |
|---|---|---|---|
| **Current state** | `CLAUDE.md` (Mac entry point + controller) | **every session** | what IS true now + the **last 2 session blocks** only |
| **History** | controller `~/minicloud-ktaylorganisation/CLAUDE-history.md` | on demand | older session blocks + full phase log (append-only archive) |
| **Facts / gotchas** | memory system (`memory/*.md`, index `MEMORY.md`) | **selective recall** | reusable gotchas, references, project/user facts |
| **Stable rules / runbooks** | `.claude/rules/*.md` (this repo, git) | **auto-loaded** | conventions, runbooks, standards |

## Hard rules
1. **CLAUDE.md holds the last 2 session blocks, no more.** Adding a 3rd → move the **oldest** block to `CLAUDE-history.md` (append, with a dated `<!-- archived … -->` separator).
2. **Reusable gotchas go to the MEMORY system, not into a session block.** A session block may *mention* a gotcha in one line and link the memory (`[[name]]`); the detail lives in the memory file (recalled selectively, not always loaded). Do **not** re-narrate the same gotcha in prose every session.
3. **Runbooks/conventions** belong in `.claude/rules/*.md`, not re-stated in CLAUDE.md.
4. **Soft cap:** Mac `CLAUDE.md` ≤ ~2,500 words / ~120 lines. The controller `CLAUDE.md` may be larger (it also carries operational runbooks) but its **session blocks are still capped at 2**.
5. Both files keep a **`## Knowledge map`** block near the top pointing to history / memory / rules.

## End-of-session procedure (every "sync both CLAUDE.md")
1. **Prepend** the new session block (both files).
2. **Migrate** any session block now beyond the newest 2 → append to `CLAUDE-history.md` (controller).
3. **Refresh** the current-state facts in place (don't just append — overwrite what changed).
4. **Extract** any durable gotcha discovered → a memory file (+ `MEMORY.md` line); reference it from the block, don't duplicate it.

## Compaction procedure (when a file drifts past the cap)
- **Always back up first** (`cp CLAUDE.md CLAUDE.md.bak`, same for history) — reversible.
- Keep: header + `Knowledge map` + last 2 session blocks + (controller) the runbook sections.
- Archive the rest to `CLAUDE-history.md` (append; never delete outright).
- Verify: line/word counts before→after + that the archive grew by the removed amount.
- Reference implementation: the 2026-08-29 compaction (Mac 215→86 lines/7k→1.5k words; controller 590→227 lines, 372 archived).
