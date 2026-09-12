# AGENTS.md — minicloud-gitops

Context bridge for any coding agent (Claude Code, Codex, …). Kept **tiny on purpose**: the code +
the files below are the source of truth; this file only routes you to them and states what the repo
cannot (policy, catches, pitfalls). Don't add repo overviews/trees/stack here — they rot (see
`.claude/rules/bmad-compliance.md` *Existing-codebase context*).

## Read these first (authoritative — not this file)
- **`.claude/rules/*.md`** — the constitution (auto-loaded for Claude; **Codex must read them**):
  `gitops.md` (Helm golden path + Kargo + registry), `conventions.md`, `testing.md`,
  `github-projects.md`, `bmad.md` + `bmad-compliance.md` (delivery model), `connectivity.md`.
- **`README.md`** — the Repository map (role of each dir).
- **Source of truth for *state*:** `git log`/`git status` + the **GitHub Project boards** (#2–#17) +
  Kargo/ArgoCD live state. There is **no** `CURRENT-STATE.md`/`HANDOFF.md` — verify against the repo,
  not a narrative doc. `CLAUDE.md` is **local/controller only, never committed** — do not add it.

## What this repo is
A **GitOps deploy repo** — only what ArgoCD reconciles (Applications, wrapper/library Helm charts,
platform manifests, env overlays) + ADRs. **No application source, notebooks, or dev scripts** (see
`.gitignore`). App code lives in each product's own repo.

## Hard rules (never violate — the platform enforces these)
- **Git is the only write path.** Never `kubectl apply`/`argocd app sync` a managed workload by hand —
  change Git, let ArgoCD reconcile. Promotion is **Kargo → CODEOWNERS-gated prod PR → ArgoCD**.
- **Prod is CODEOWNERS-gated** (`@AndreLair`): `services/*/helm|base|kargo/`, `apps/`, `helm-values/`,
  `manifests/{quotas,network-policies}/*-prod`. Prod change = a PR on that gate, never a direct edit.
- **Secrets via ESO→Vault only.** Never hardcode/commit a secret; `MINICLOUD_CA_CERT` is raw PEM (never base64-decode).
- **Smallest safe change.** Don't rewrite working architecture, delete tests, or refactor unrelated modules.

## Catches (what configs don't tell you)
- From the Mac, kubectl needs `--context minicloud` (default context is wrong); on the **controller** use plain `kubectl` (no `--context`). Use `/usr/bin/curl` (+ `--cacert ~/minicloud-ca.crt`), not anaconda's.
- A custom app = a **wrapper Helm chart** at `services/<svc>/helm/` depending on the `minicloud-app-deployment` library chart. Validate locally: `cd services/<svc>/helm && helm dependency update . && helm template <svc> . -f values-dev.yaml`. Commit `Chart.lock`; `charts/` is gitignored; `helm.releaseName` is mandatory; escape non-Helm `{{ }}`.
- `gh pr create/merge` has glitched here (spurious GraphQL errors) → fall back to `gh api .../pulls` + `/merge` (REST).

## Start-of-task
`git status` → read the one relevant `.claude/rules/*.md` → make the smallest safe change → run the
relevant checks (`testing.md` L0–L4; `helm template` for charts) → PR (CODEOWNERS gate does the rest).
Pick a **BMAD delivery path** by size (A small / B feature / C new product / E hotfix — see
`bmad-compliance.md`); a one-line fix does not need a PRD.
