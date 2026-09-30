# Intent: harden the SDLC harness to be AI-native

Author: AndreLiar (platform owner). Status: in-progress → tracked as epic #1497.

> Dogfood example — this is the actual intent behind the AI-native SDLC hardening, written
> after a gap analysis against Anthropic's 12-play playbook. Kept as a worked reference.

## Problem
The platform builds strong governance around code (BMAD, Gatekeeper, CODEOWNERS, cosign,
QA gate) but the **agentic connective tissue** is thin: no client-side deterministic
guardrails, policy lives only in always-loaded rules (not triggered Skills), PR review /
config-regression / production-signal → work are all manual and un-encoded. As agents write
most of the diff, the stages *around* build (guardrails, review, evals, the maintenance
loop) are the bottleneck.

## Proposed outcome
The 12 plays are in place in dependency order, so: dangerous/forbidden agent actions are
blocked at the keystroke; institutional policy fires contextually; every PR gets a
consistent review pass; the agent config is regression-tested; and a production control-band
breach opens an `intent.md` that re-enters this same loop. Humans stay on the gates.

## Affected users and systems
The owner (as operator + reviewer); `minicloud-gitops` (hooks/rules/skills/commands/evals);
`minicloud-ops` (the closing-the-loop detector); every product repo that adopts the pattern.

## Constraints
- **No metered model surplus** — Claude parts run on the existing Claude Code plan or
  deterministically; only free/deterministic checks run in CI (owner decision).
- Server-side gates (CODEOWNERS/Gatekeeper/CI/cosign) remain the enforcement of record;
  hooks/skills are the fast client layer, not a replacement.
- Fail-open guardrails (a hook bug must never wedge the agent).

## Open questions
- Commit the validated `spec.md`/`sprint-status.yaml` for regulated work (currently
  git-ignored in `_bmad-output/`)? — flagged in #1497, undecided.
- When (if ever) to enable subscription-OAuth CI automation for review/evals.
