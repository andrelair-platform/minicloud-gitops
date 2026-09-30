# Plan: <change title> (from intent/<slug>.md or issue #NNN)

> AI-native SDLC Play 3. Produced by Claude Code **plan mode** before any code is written;
> commit the approved version so the PR review (`REVIEW.md`) can check the diff against it.
> Update this file in the **same commit** when the implementation deviates.

## Files that change
<the exact paths that will be added/edited>

## Order of work
1. <step — smallest safe increment first>
2. <step>
3. <step>

## Risks
<what could break; the single riskiest step; rate limits / quotas / a gated path touched;
whether it crosses a security or architecture boundary (→ needs the governance gate)>

## Proof
<the tests/checks that prove it — the exact commands; what the `verifier` subagent should
run; the expected result (e.g. "evals green", "helm template renders", "endpoint 200 with
the new field", "un-auth request 302s")>
