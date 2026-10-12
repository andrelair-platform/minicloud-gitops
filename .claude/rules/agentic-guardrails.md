# Agentic Guardrails — Claude Code hooks (the deterministic layer behind advisory rules)

Part of the **AI-native SDLC** hardening (Anthropic playbook Play 6 *build-time
guardrails* + Play 11 *approval gates*). The `.claude/rules/*.md` constitution is
**advisory** — Claude is *likely* to follow it, but nothing forces a session to. A
**hook** is the deterministic layer: a script that runs *before* (or after) a tool
call and can **allow, block, or inform**, on every session, unbypassable by a prompt.

> Rule of thumb (from the playbook): write a Skill/rule for knowledge that should be
> applied consistently; put a **hook** behind anything that must hold **without
> exception**. The rule makes violations rare; the hook makes them (near-)impossible.

## What's wired (this repo)

Config: `.claude/settings.json` (committed, CODEOWNERS-gated). Scripts: `.claude/hooks/`.
Hooks are **project-scoped** — they apply when Claude Code runs with `minicloud-gitops`
as the project root. (The workspace-root `CLAUDE.md` and other repos are unaffected.)

| Hook | Event · matcher | Blocks (exit 2) — and the rule it enforces |
|---|---|---|
| `guard-bash.py` | PreToolUse · `Bash` | `rm -rf` of a catastrophic root (`/ /* ~ $HOME . ..`); force-push to `main/master` (branch strategy); **manual ArgoCD mutation** `argocd app sync\|rollback\|patch\|set` ([[feedback_never_manual_argocd_sync]], gitops.md); `kubectl delete namespace\|ns`; `curl\|wget … \| sh` (supply-chain); `git add … CLAUDE.md` ([[feedback_claude_md_repo_rule]]). Also scans the remote command inside `ssh host "…"`. |
| `guard-write.py` | PreToolUse · `Write\|Edit\|MultiEdit` | literal **secret material** in new content (private keys, `AKIA…`, Vault `hv[sb].…`, `ghp_…`, `github_pat_…`, Slack/GitLab tokens → secrets go to Vault→ESO, gitops.md); edits under `services/*/helm/charts/` (vendored, gitignored); anything under `.git/`; creating a `CLAUDE.md` in-repo ([[feedback_claude_md_repo_rule]]); **creating a NEW `manifests/<subdir>`** (FROZEN — ARCHITECTURE.md) and **application source code** (`*.py/*.go/*.ts`) outside `scripts/`/`evals/`/`.claude/`/`.github/` (deployment-repo rule, conventions.md). The last two are **creation-only** — editing an existing manifests file or code file is never blocked (so the LOT E content moves still work). |
| `validate-yaml.py` | PostToolUse · `Write\|Edit\|MultiEdit` | *advisory* — after editing a **plain** `.yaml/.yml`, fast `safe_load_all` syntax check (exit 2 feeds the parse error back so Claude fixes it). Skips `templates/` + any file with `{{`/`${{` (Helm/Kargo), and no-ops if PyYAML is absent. |

## Design principles (keep these when extending)

1. **Fail-open.** Any parse error / unexpected input → **exit 0**. A hook bug must
   never wedge the agent. Only a *matched* dangerous pattern exits 2.
2. **First-token dispatch.** `guard-bash.py` splits the command into segments and
   dispatches on the *executable* — so `grep "argocd app sync"` or `echo rm -rf /`
   is NOT blocked, only the real invocation is. Near-zero false positives.
3. **Narrow > broad.** Block the unambiguously-catastrophic/forbidden; do **not**
   blanket-block a whole verb (e.g. `kubectl rollout restart` stays allowed — it's a
   legitimate op; only `delete namespace` is refused). False positives erode trust and
   get hooks disabled.
4. **Self-explaining blocks.** Every block prints *why* + *the sanctioned path*
   (e.g. "prod moves via a CODEOWNERS PR → Kargo; a human runs the wedge-exception
   directly"). A blocked human/agent must know what to do next.
5. **Agent-blocked ≠ human-blocked.** For the ArgoCD/namespace gates the *agent* is
   refused; the human operator retains the documented exception by running it directly.
   That is the *approval-gate* pattern (Play 11): the gate is on automation, not people.

## Relationship to the server-side gates (defence in depth)

Hooks are the **fast client-side layer**; they do **not** replace the enforcement of
record. Prod safety still rests on **CODEOWNERS** (gated paths), **Gatekeeper/OPA**
(admission), **CI** (Trivy/checkov/kubeconform/cosign), signed commits, and the
**change-record** audit. Hooks catch mistakes *at the keystroke*, before they ever
reach a PR or the cluster.

**Architecture taxonomy — paired agent + server gate (remediation-plan.md Stage 6).** The
repo's `platform/` vs `is/` + `apps/` taxonomy (ARCHITECTURE.md) is enforced on two layers:
the `guard-write.py` rules 5–6 above (keystroke) **and** the server-side
`.github/workflows/architecture-guard.yml` CI check, which fails any PR that ADDS a new
`manifests/<subdir>`, an `apps/` Application outside `apps/platform/<layer>/`|`apps/is/<group>/`,
a new top-level dir without an ADR, or application source code. The CI check inspects only
PR-**added** files (`--diff-filter=A`) so the pre-existing legacy state (`apps/workloads/`, the
`manifests/` LOT E residue) is grandfathered — only *new* rot is blocked.

## Test / extend

```bash
# unit-test a hook by piping the Claude Code hook JSON on stdin:
echo '{"tool_input":{"command":"rm -rf /"}}'      | python3 .claude/hooks/guard-bash.py ; echo "exit $?"   # 2
echo '{"tool_input":{"command":"git status"}}'    | python3 .claude/hooks/guard-bash.py ; echo "exit $?"   # 0
# guard-write taxonomy rules (CLAUDE_PROJECT_DIR must point at the repo root):
echo '{"tool_input":{"file_path":"'"$PWD"'/manifests/newdir/x.yaml","content":"a: b"}}' | python3 .claude/hooks/guard-write.py ; echo "exit $?"  # 2 (new manifests subdir)
echo '{"tool_input":{"file_path":"'"$PWD"'/platform/ai/app.py","content":"x"}}'          | python3 .claude/hooks/guard-write.py ; echo "exit $?"  # 2 (app code outside allowed)
echo '{"tool_input":{"file_path":"'"$PWD"'/scripts/x.py","content":"x"}}'                 | python3 .claude/hooks/guard-write.py ; echo "exit $?"  # 0 (tooling code allowed)
```

- **Add a rule to a block:** extend the regex/first-token dispatch in the relevant
  script, then add an allow-case **and** a block-case to the test matrix above.
- **Adopt in another repo:** copy `.claude/hooks/` + `.claude/settings.json` into that
  repo (they're self-contained, stdlib-only except the optional PyYAML in validate-yaml).
- **Non-bypassable / MDM:** for a hard org-wide floor (`allowManagedHooksOnly`, sandbox,
  permission deny-lists) use *managed settings* deployed outside the repo — deferred;
  the repo-committed hooks above are the current layer.
