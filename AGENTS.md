# AGENTS.md — minicloud-gitops

Context bridge for any coding agent (Claude Code, Codex, …). Kept **focused on policy**: the code +
the files below are the source of truth; this file only routes you to them and states what the repo
cannot (policy, catches, pitfalls). Don't add repo overviews/trees/stack here — they rot (see
`.claude/rules/bmad-compliance.md` *Existing-codebase context*).

## Read these first (authoritative — not this file)
- **`.claude/rules/*.md`** — the constitution (auto-loaded for Claude; **Codex must read them**):
  `gitops.md` (Helm golden path + Kargo + registry), `conventions.md`, `testing.md`,
  `github-projects.md`, `bmad.md` + `bmad-compliance.md` (delivery model).
- Some rule files retain explicitly historical migration examples. Where they conflict, current
  executable Applications/wrappers and the Git-only hard rules below prevail; report the drift.
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

## Operational safety for GitOps work

The workspace-wide evidence, investigation, read-only-operations, risk, and validation rules in the parent `AGENTS.md` apply here. The rules below specialize them for Kubernetes and GitOps; they do not replace the hard rules above.

### Classify ownership and delivery before editing

For every change, identify the source-of-truth file, Argo CD Application/ApplicationSet or other consuming controller, target namespace/environment, and downstream resources. Never modify a rendered object or live Kubernetes resource when Git owns it.

Do not assume every workload uses the golden path. Classify it first as:

- Kargo single-image promotion;
- Kargo multi-image promotion;
- legacy CI-driven GitOps mutation;
- vendor chart reconciliation; or
- another mechanism proven by executable configuration.

The preferred promoted-service path is GitHub Actions → immutable SHA image → Harbor/GHCR → Kargo → GitOps PR → Argo CD → Kubernetes. Do not implicitly migrate a legacy or vendor deployment path while making an unrelated change. The current platform standard is dev + prod; treat references to staging as potential drift and verify before acting.

### Production gates and environment isolation

Before a production change, document blast radius, dependencies, expected downtime, rollback, data/storage impact, secrets impact, networking impact, required telemetry, and validation. Never bypass protected PRs, CODEOWNERS, Kargo promotion/verification, or Argo CD Git reconciliation except under an explicitly authorized and documented emergency procedure. Verify that dev and prod image references, values, namespaces, Vault paths, databases/PVCs, ingress, quotas, and policies remain isolated as intended.

### Connectivity and NetworkPolicy

Never introduce `allow-all` as a troubleshooting shortcut. Establish the source workload/namespace, destination workload/namespace, namespace labels, pod selectors, port/protocol, DNS egress needs, Service endpoints, and both ingress and egress enforcement. Inspect standard NetworkPolicy and CiliumNetworkPolicy, then implement the smallest required rule.

A genuinely necessary broad incident exception must be explicitly temporary, documented, reviewed, time-bounded where possible, and replaced with least privilege afterwards. It requires explicit authorization because it changes the live security boundary.

### Secrets and Vault

Application runtime secrets predominantly flow Vault → ESO → Kubernetes Secret → workload, but bootstrap/platform exceptions exist. Trace metadata only: Vault path → auth role → ExternalSecret/ClusterSecretStore → Kubernetes Secret name/key → workload reference. Never print secret values, expose them in logs, commit credentials, or replace ESO with a plaintext Secret for convenience.

For Vault incidents, classify separately:

- immediate runtime impact;
- restart-time impact while materialized Secrets still exist or are absent;
- deployment-time impact;
- refresh/rotation impact;
- certificate issuance/renewal impact; and
- Vault restart/auto-unseal impact.

Include Longhorn/Raft storage, AWS connectivity, AWS KMS, the `vault-kms-credentials` bootstrap Secret, ESO, and cert-manager where applicable. Do not reduce the conclusion to “applications fail when Vault is down.”

### Stateful and security-sensitive resources

Before changing StatefulSets, PVCs, Longhorn, Vault, PostgreSQL, Qdrant, ClickHouse, NATS JetStream, Temporal, or any persistent service, establish storage class/mechanism, backup and tested restore coverage, replication, rollout/rollback behavior, migration requirements, and irreversible steps. Never delete or recreate persistent resources as a deployment fix without explicit authorization.

Inspect an equivalent working Minicloud implementation before adding Helm wrappers, CI, Kargo, Argo CD, ESO/Vault wiring, NetworkPolicies, monitoring, ingress/certificates, quotas, probes, or resources. Prefer the established pattern. If a materially different pattern is better, surface the architecture decision and trade-offs before implementation.

Treat changes to RBAC, privileged/hostPath workloads, Linux capabilities, Gatekeeper/PSS exceptions, public ingress, Vault/secret stores, admission controls, image provenance, TLS verification, or broader network access as security-sensitive and explain their blast radius before editing.

### GitOps validation report

Apply the relevant levels from `testing.md`. For manifest/chart changes, render every affected environment and inspect object names, selectors, immutable fields, image references, secrets references, PVCs, and object-set differences. Run available YAML/schema, policy, Checkov, workflow, and Git diff checks. Report what ran, what could not run, risk, rollback, and remaining unknowns; repository rendering is not proof that the live cluster reconciled successfully.

## Start-of-task
`git status` → read the one relevant `.claude/rules/*.md` → make the smallest safe change → run the
relevant checks (`testing.md` L0–L4; `helm template` for charts) → PR (CODEOWNERS gate does the rest).
Pick a **BMAD delivery path** by size (A small / B feature / C new product / E hotfix — see
`bmad-compliance.md`); a one-line fix does not need a PRD.
