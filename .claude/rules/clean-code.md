# Clean Code Standard — the build-time quality floor (deterministic where it can be)

What "clean code" means on this platform, stated as a **standard** so it's a build gate, not a matter of
whether a reviewer happened to notice. This file owns the **WHAT** (the practices); `code-review.md` owns
the **review lens** that judges them; `testing.md` **L0** owns the **mechanical enforcement** (linters +
formatters that fail CI). The three are paired — this one makes "caught in review if someone notices" into
"the pipeline rejects it."

> **The one principle (inherited from `code-review.md`):** every change must **leave the overall code
> health better, or at least no worse.** There is no perfect code — only *better* code. Clean code is not
> polish for its own sake; it is what keeps a solo-plus-AI codebase legible and changeable a year later
> (the `ai-native-engineering.md` rebuild test: *could the owner re-derive this?*).

## The practices (the standard — what every change is held to)

| Practice | The rule | Why |
|---|---|---|
| **SRP** | one function/class/module = **one reason to change**; one level of abstraction per function | the module-level form is `architecture-strategy.md` (cohesion/coupling) — this is its function-level twin |
| **YAGNI / no speculative generality** | solve **today's** problem; no "flexible" hooks, config, or abstraction for a use case that doesn't exist yet | `code-review.md` *Complexity*; over-engineering is a review blocker, not a nicety |
| **DRY — but WET first** | extract a duplication on the **third** occurrence, not the second (two similar-looking things often diverge). A *wrong* abstraction costs more than a little duplication | premature DRY couples things that should stay independent |
| **Naming** | names say **what they are / do**; no single-letter (except loop indices / math), no `data`/`tmp`/`mgr` vagueness, no abbreviations the domain doesn't use. A good name removes the need for a comment | the next reader (often the AI) navigates by names |
| **Functions small + shallow** | prefer short functions; **cap cyclomatic complexity** and nesting (limits below). Deep nesting → early-return / guard clauses / extract | enforced by linters, not taste |
| **Comments explain WHY, not WHAT** | the code says what; a comment says *why this way* (the trade-off, the gotcha, the link to the ADR/issue). **Delete commented-out code** (git holds it). Flag stale comments | a WHAT-comment rots the moment the code changes |
| **Error handling is explicit** | never silently swallow an error; **wrap with context**; fail **fast + loud** at boundaries; no bare `except:` / ignored `err` / floating promise. Money/auth/state paths must surface failure | the alembic-fileConfig + unauth-API class (`qa-gate.md`) started as a swallowed/assumed path |
| **No magic numbers/strings** | a literal with meaning gets a **named constant** (timeouts, limits, statuses, eurocent factors) | a named constant is self-documenting and greppable |
| **Immutable + pure where practical** | prefer pure functions + immutable data for business logic (the `rate()` engine seam is the reference); push I/O to the edges | pure logic is unit-testable without mocks (`testing.md`) |
| **Consistency beats personal style** | match the surrounding code + the linter; the **style guide / formatter is authoritative** — don't hand-impose a different style | `code-review.md` *Consistency* |
| **Delete, don't accumulate** | dead code, unused params, unreachable branches, TODO graveyards → removed. A real deferral → `deferred-work.md` or a `TODO(#issue)`, never a bare `TODO` | `bmad-compliance.md` deferred-work discipline |

**Scale by delivery path (`bmad-compliance.md`).** This is always-on at the **mechanical floor** (L0 runs
on every push, every path). The **judgement** practices (SRP/DRY/naming/abstraction) are held firmly on
Path-B/C feature code and lightly on a Path-A/E one-liner — the linter floor still applies, but don't
block a hotfix on a naming `Nit:`.

## Deterministic enforcement — the linter config IS the standard (not prose)

The practices above become a **gate**, not advice, by encoding the measurable ones in each repo's **L0
linter config** (so CI fails, exactly like formatting does). These are the **house defaults** — a repo may
tighten them, and may loosen a specific rule only with an inline justification (rule 5 of `testing.md`).

| Stack | Tool | The clean-code rules to enable | Measurable limits (house default) |
|---|---|---|---|
| **Python** | **ruff** | `C901` (mccabe), `PLR` (pylint-refactor: too-many-args/branches/statements/returns), `N` (pep8-naming), `SIM` (flatten/simplify), `RET` (early-return), `ARG` (unused args), `B` (bugbear), `TRY`/`BLE` (no blind `except`), `ERA` (no commented-out code) | `mccabe.max-complexity = 10`; `pylint.max-args = 6`; `pylint.max-branches = 12` |
| **Go** | **golangci-lint** | `gocyclo`/`gocognit` (complexity), `funlen`, `revive` (naming), `errcheck` + `wrapcheck` (handle+wrap errors), `ineffassign`, `unparam`, `unused`, `nestif` | `gocyclo.min-complexity: 15`; `funlen: 80 lines/40 stmts`; `nestif.min-complexity: 5` |
| **TypeScript** | **eslint** (+ `tsc` strict) | `complexity`, `max-lines-per-function`, `max-params`, `max-depth`, `@typescript-eslint/naming-convention`, `@typescript-eslint/no-floating-promises` (error handling), `no-console` (use the logger), `eqeqeq` | `complexity: 10`; `max-params: 4`; `max-depth: 4`; `max-lines-per-function: 80` |
| **YAML/Helm** | yamllint + kubeconform | consistency/indent (already L0) | — |

**The rest stays judgement** (SRP intent, is-this-the-right-abstraction, is-this-name-good, does-a-comment-
explain-why) — caught at the `code-review.md` fresh-context pass + the human review, labelled with the
`Nit:`/`Optional:`/`FYI:` severities. A linter cannot decide whether an abstraction is *correct*, only
whether a function is *too long*. Encode what's measurable; review the rest.

## How it plugs into the existing gates (don't double-count)
- **`testing.md` L0** runs these linters on every push — **this is where the measurable rules are enforced**
  (fail-fast, before L1). A new repo's lint config MUST enable the rows above (a New-Repo / DoD item,
  `conventions.md` + `bmad-compliance.md`).
- **`code-review.md`** judges the non-mechanical practices (Design/Complexity/Naming/Comments/Consistency)
  at the fresh-context + human layers — it now **references this file** as the definition of what "clean"
  means.
- **`agentic-guardrails.md`** hooks block the catastrophic (secrets, conflict markers) at the keystroke —
  orthogonal to style; those are safety, this is quality.
- **`architecture-strategy.md`** is the module/service-level twin (SRP/cohesion/coupling across modules);
  this file is the function/file level. Read together.

## Don't
- Don't treat clean code as cosmetic polish that blocks a merge — the bar is *improves health*, not *perfect*.
- Don't DRY on the second occurrence, or add a config flag / abstraction for a use case that doesn't exist (YAGNI).
- Don't leave a measurable rule (complexity/length/naming) to the reviewer's eye when a linter can enforce it — **encode it**.
- Don't loosen a linter rule without an inline comment saying why (`testing.md` rule 5).
- Don't write a WHAT-comment or leave commented-out code; don't swallow an error to make a path "work".

Related: `code-review.md` (the review lens), `testing.md` (L0 enforcement + the layer pyramid),
`architecture-strategy.md` (module-level clean code), `ai-native-engineering.md` (the rebuild test),
`bmad-compliance.md` (path sizing + deferred-work), `conventions.md` (repo standardisation / New-Repo gate).
