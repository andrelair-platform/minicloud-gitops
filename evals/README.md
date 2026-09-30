# Agent-config evals (Play 9)

Regression-tests the **agent operating config** (`.claude/hooks`, `rules`, `skills`,
`commands`, `settings.json`) — the config *steers* every session, so it deserves the same
regression testing as code. Two layers, split by cost:

## Layer 1 — deterministic, FREE, runs in CI

No model calls. Runs automatically on any `.claude/**` or `evals/**` change
(`.github/workflows/agent-config-evals.yml`) and locally:

```bash
python3 evals/test_hooks.py          # allow/block matrix for the 3 hooks
python3 evals/lint_agent_config.py   # skills/commands frontmatter, settings.json, hooks compile
```

`test_hooks.py` is the guard against a future edit silently breaking a guardrail (widening a
regex so `rm -rf ./build` gets blocked, or narrowing one so `argocd app sync` slips through).
**When you add or change a hook rule, add an allow-case AND a block-case here** — that is the
Definition of Done for a hook change.

## Layer 2 — model-based, ON-PLAN, run locally on demand

These *do* call Claude, so they run through **Claude Code on the owner's existing plan**
(never a metered CI job / API key). Trigger them manually when the rules/skills change and you
want to check that the agent still *behaves* to standard:

```bash
bash evals/agent/run-local.sh        # runs each evals/agent/*.md case via `claude -p`
```

Each case in `evals/agent/` is a prompt + the expected behaviour (e.g. "asked to promote to
prod, the agent cites the QA gate and refuses a hand-edited tag"). This is the AI-native
playbook's Play 9 "eval on config change", kept on-plan and manual by design — the deterministic
Layer 1 is the CI gate; Layer 2 is the deeper, occasional check.

> Optional automation upgrade (not enabled): run Layer 2 in CI via `claude-code-action`
> authenticated with a **subscription-OAuth token** (`claude setup-token`) so it bills the plan,
> not the API — subject to your plan's rate limits/terms.
