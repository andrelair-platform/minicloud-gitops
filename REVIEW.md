# REVIEW.md — platform PR review policy

The single source of truth for **what a PR review checks**. Consumed by the local
`/review-pr` command (runs on the owner's Claude Code plan — **no CI/API cost**) and,
if automation is enabled later, by a `claude-code-action` (Anthropic playbook Play 10).

Reviews **inform** the merge decision; they do **not** approve it. The human **CODEOWNERS**
gate remains the approval of record.

## Passes — tag every finding with its pass + severity

1. **Bugs** — logic errors, broken edge cases, subtle regressions, wrong error handling,
   off-by-one, money/units, unhandled failure modes.
2. **Security** — authn/authz gaps, secret material in the diff or logs, PII exposure,
   egress/NetworkPolicy holes, injection, supply-chain. Cross-check the
   `secure-api-review` skill.
3. **Compliance-with-intent** — the diff matches the stated `plan.md`/`spec.md` (if the
   change has one) **and** the `.claude/rules/*` constitution.

## Platform must-checks (this repo is GitOps + regulated)

- **Prod-gate integrity** — does the change touch a CODEOWNERS-gated path
  (`services/*/helm`, `services/*/base`, `apps/`, `manifests/*-prod.yaml`, `helm-values/`,
  `manifests/kargo/`, `.claude/{settings.json,hooks,rules,skills}`, `bootstrap/`,
  `manifests/rbac/`)? Flag anything that **weakens** a gate.
- **Immutable image tags** — no hand-edited image tags (Kargo owns them via git-Warehouse);
  prod pins a **ghcr SHA**, never `:latest`.
- **Secrets** — no plaintext secret material anywhere; secrets are Vault→ESO only.
- **Agent-config changes** — a change to `.claude/{hooks,settings.json,rules,skills}` alters
  what the agent is allowed to do → review as **security-relevant**; confirm hooks still
  fail-open and their test matrix is updated.
- **Helm/YAML** — does it `helm template` cleanly? non-Helm `{{ }}` escaped? cert **ECDSA**?
  immutable selector for zero-downtime? ArgoCD single Helm source + `releaseName`?
- **Testing pyramid** — a Tier-A change without L2/L3/L4 (only unit) is **not** Done
  (testing.md); every mocked boundary needs a contract/integration test behind it.

## Important vs Nit

Reserve **Important** for a finding that would break behaviour, leak data, weaken a
prod/security gate, or violate a rule. Style and naming are **Nits**.

## Cap the nits

Report at most **5 nits**; summarize the rest as a count.

## Do not report

Generated files, vendored `**/charts/`, anything CI already enforces (checkov / kubeconform
/ Trivy / cosign / signed-commits), and pre-existing issues outside the diff.

## Output format

1. A one-line **verdict**: `SHIP` (no Important findings) or `FIX-FIRST`.
2. Findings grouped by severity — **🔴 Important** then **🟡 Nit** — each tagged
   `[Bugs|Security|Compliance]`, with `file:line` and the concrete fix.
3. If the change touches a security/architecture boundary (auth, data model, netpol,
   secrets, public API, IAM, registry), say so explicitly — that needs the governance gate
   (bmad-compliance.md), not just CODEOWNERS.
