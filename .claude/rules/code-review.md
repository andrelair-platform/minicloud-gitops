# Code Review Standard — reviewer discipline (adapted from Google eng-practices)

How we review a change on this platform. Adapted from **Google's Engineering Practices — "How to do a code
review"** (`https://google.github.io/eng-practices/review/reviewer/`) and mapped onto our real review
machinery: the **three review layers** (`bmad-compliance.md`), **CODEOWNERS** (`gitops.md`), the **live QA
gate** (`qa-gate.md`), the **test pyramid** (`testing.md`), and the **docs DoD gate** (`documentation.md`).

> **Our reviewer reality (the adaptation).** Code here is largely written by **AI agents**, reviewed in
> **three layers**: (1) `/bmad-build` self-review, (2) **`/bmad-code-review` in a FRESH context** — the
> independent pass that has no memory of writing the code (this *is* the "second pair of eyes"), (3) the
> **human CODEOWNERS** approval that gates prod. Google's reviewer principles apply to layers 2 + 3; the
> owner is the final reviewer. Scale review depth by **delivery path** (A/B/C/E — `bmad-compliance.md`).

## The Standard — the one principle above all
> **Approve a change once it DEFINITELY IMPROVES the overall code health of the system — even if it isn't
> perfect.** There is no perfect code, only *better* code. The reviewer's job is to stop health from
> degrading, **not** to block forward progress on polish.

- Codebases rot through **small** health decreases under time pressure — guard against that, but don't
  demand flawlessness.
- A merely-preferred improvement → prefix **`Nit:`** (non-blocking). A teaching point → say so.
- **Facts & data > opinion. Design is engineering, not taste** (`architecture-strategy.md`). The **style
  guide / linters are authoritative**; on anything they don't cover, follow the existing pattern — don't
  impose personal style. **Consistency wins** unless the existing pattern genuinely degrades health.
- **Never deadlock a change over a disagreement.** Resolve on principle; if stuck, escalate (owner call /
  an ADR) — a stalled CL helps no one.

## What to look for (the reviewer checklist — in priority order)
| Focus | What to check | Our hook |
|---|---|---|
| **Design** (most important) | do the pieces fit? does this belong here vs a module/library? boundary-crossing? | SA artefact set; `architecture-strategy.md` (module vs new service); the governance gate |
| **Functionality** | does it do what's intended + good for users? **edge cases, concurrency (races/deadlocks), think like a user** | the live **QA gate** (`qa-gate.md`) is the backstop |
| **Complexity** | simpler possible? **no over-engineering / speculative generality** — solve today's problem (YAGNI) | `architecture-strategy.md` anti-patterns |
| **Tests** | right layers **in the same CL**; tests **actually fail when code breaks**; not mock-only | `testing.md` L0–L4 + tier rules; **traceability matrix** for Path C |
| **Naming / Comments** | names say what they are; comments explain **why**, not what; flag stale comments/TODOs | — |
| **Style** | linter-clean; `Nit:` for non-mandatory; **keep style changes out of a logic CL** | CI L0 (ruff/golangci/eslint/yamllint) |
| **Consistency** | matches the codebase; file a cleanup bug for pre-existing drift rather than block | — |
| **Documentation** | READMEs / as-built map / ADR / runbook updated **in the same effort** | `documentation.md` DoD gate; `documentation-standard.md` |
| **Every line** | read **every** assigned line; can't understand it → ask (next reader won't either); pull a specialist for security/concurrency/a11y | — |
| **Context** | judge the diff against the **system as a whole** — is the file/system getting more complex overall? | — |
| **Good things** | **call out what was done well** — mentoring value is often higher than catching a flaw | `evidence-and-proof.md` |

## Navigating a review (the order)
1. **Broad view first** — read the description; should this change exist *at all*? If not, say so **now**,
   politely, with reasoning + an alternative.
2. **Main parts first** — review the core-logic file(s) first and **send major design feedback immediately**
   (before the rest) — a redesign is cheapest caught early. If the change is too big to find the core →
   ask to **split into small, stackable CLs**.
3. **The rest in sequence** — once no major flaw remains, go file-by-file; **read the tests first** to learn
   what it's meant to do. (`/bmad-walkthrough` for risky diffs — auth/schema/public-API/security.)

## Speed
- **Respond within one business day** (not necessarily *finish* — respond). Fast *responses* matter more
  than fast *turnaround*: many quick round-trips beat one slow pass.
- Don't interrupt your own focused work to review — do it at a natural breakpoint; the context-switch cost
  to you exceeds the brief wait.
- **`LGTM` + comments** when you trust the author to handle the minors (the AI layer makes this cheap).
- **Never trade the standard for imagined velocity.** The real speed-up is the compounding effect of
  consistent standards + fast responses + the AI first-pass.

## How to write review comments
- **Comment on the code, never the person.** *"This concurrency adds complexity with no benefit I can see →
  single-threaded is better here,"* not *"why did **you** use threads?"*
- **Explain why** — your intent / the best practice / how it improves health, not just a directive.
- **It's the author's job to fix it, not the reviewer's** — prefer **pointing out the problem** (they learn,
  often find a better fix); give a direct prescription only when it genuinely helps/speeds.
- **Label severity explicitly:** **`Nit:`** (trivial) · **`Optional:`/`Consider:`** (good idea, not required)
  · **`FYI:`** (informational, not this CL). Unlabelled = expected to address.
- **Unclear code → ask them to REWRITE it, don't accept an explanation in the PR thread** — *"explanations
  written only in the review tool don't help the next reader."* Push clarity into the code/comments.

## Handling pushback
- **The author may be right** — they're closer to the code; if their reasoning holds on *health* grounds,
  concede. Otherwise keep advocating, politely, showing you *heard* them (health improves in small steps).
- **Politeness, not leniency, prevents upset** — resentment comes from *how* a comment is written, not from
  insisting on quality.
- **"I'll clean it up in a later CL" → no.** New complexity is **cleaned up before submission unless it's an
  emergency**. Pre-existing/out-of-scope problems → **record them** in `deferred-work.md` (or a filed issue
  + a `TODO(#issue)`), don't block but don't let them vanish. (This is our `deferred-work.md` discipline.)

## Relationship to the gates (don't double-count)
Review (this) + **CI** (`testing.md` L0–L4) + the **live QA gate** (`qa-gate.md`, L5) + **CODEOWNERS**
(the merge enforcement) are **distinct** evidence — none replaces another. This file governs *human/AI
judgement*; CI + Gatekeeper + CODEOWNERS are the *deterministic* enforcement (`agentic-guardrails.md`).

Related: `bmad-compliance.md` (the 3 review layers + path sizing), `gitops.md` (CODEOWNERS gate),
`qa-gate.md`, `testing.md`, `documentation.md`, `ai-native-engineering.md` (comprehension > green check),
`architecture-strategy.md`. Upstream: Google eng-practices reviewer + CL-author guides.
