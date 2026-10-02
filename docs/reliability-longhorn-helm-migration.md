# Longhorn core → Helm-via-ArgoCD migration — Scoping (Finding A closure)

**Status:** ✅ **DONE (2026-10-02) — Longhorn core adopted into Helm/ArgoCD, auto-sync ON. Finding A closed.** · **Owner:** Platform · **Date:** 2026-10-02

## Outcome (2026-10-02) — executed as scoped
In-place SSA adoption via an attended, diff-gated first sync, then auto-sync enabled after verification.
- **Diff gate** (`kubectl diff --server-side --force-conflicts`): 43 objects touched, almost all Helm
  ownership labels; only real delta was +4 `CSI_*_REPLICA_COUNT` env vars on `longhorn-driver-deployer`.
- **First sync (attended, auto-sync OFF):** app `Synced/Healthy`; **60/60 volumes attached+healthy, 0
  faulted, instance-managers 0 restarts (data plane untouched), RW PVC smoke PASS.**
- **Deviation + LESSON (see below):** longhorn-manager (DaemonSet) + longhorn-ui rolled, which the diff
  gate had NOT predicted. One-time, benign, settled 6/6.
- **Auto-sync enabled** (2nd PR) after verification: `automated{prune,selfHeal}` + retry.
- **Upgrades henceforth** = bump chart `targetRevision` (one minor/hop) → CODEOWNERS PR → ArgoCD; engine
  migration via the `concurrent-automatic-engine-upgrade-per-node-limit` Setting CR in longhorn-base.

> ### ⚠️ LESSON — pod-template labels are rollout-causing, not harmless metadata
> **Helm ownership labels added under `spec.template.metadata.labels` (`app.kubernetes.io/*`,
> `helm.sh/chart`) are a pod-template change → they force a Deployment/DaemonSet rollout.** During an
> adoption diff they must NOT be bucketed with *object-level* `metadata.labels` (which don't roll). The
> first-sync diff gate under-predicted the churn because it treated all label additions as non-rolling;
> in fact the manager/ui rolled. For Longhorn the roll is safe (instance-managers = the data plane are
> separate CRs, never templated by the chart, so volumes stay served — proven here + across the 1.6→1.12
> climb). But for a **stateful workload whose own Deployment/STS carries the data**, the same adoption
> would cause a real restart — always expect a one-time rollout when adopting a running workload into Helm.
**Parent:** reliability epic #1518 · **Driver:** *Finding A* — the Longhorn **core** is installed/upgraded by
hand (`kubectl apply -f longhorn-<ver>.yaml`), outside Git/ArgoCD. The 1.6→1.12.1 climb proved the raw-apply
path works, but every hop was a manual action with no PR/review/audit trail. End state: **the core is a
Helm chart reconciled by ArgoCD**, so an upgrade = a `targetRevision` bump → CODEOWNERS PR → ArgoCD applies.

> **This is governance/operability polish, NOT a reliability gap.** The core is healthy on 1.12.1 and
> self-heals at the data plane. The win is *auditable, reviewable, reconciled* upgrades — not fixing a
> fault. Low urgency; do it on a settled cluster (it now is). It is **Path B** (an infra change crossing a
> storage boundary → the governance gate + a risk-gated cutover apply).

## Current state (grounded 2026-10-02)
| Thing | State |
|---|---|
| Longhorn core (manager DS, CSI deploys, driver-deployer, instance-managers, **25 CRDs**) | raw `kubectl apply` — `kubectl.kubernetes.io/last-applied-configuration` present, **no Helm release** (`kubectl get secret -l owner=helm -n longhorn-system` empty). Manifests recorded under `docs/longhorn-upstream/`. |
| Longhorn **settings** (`Setting` CRs), recurring-jobs, pvc-labels, backup creds/check | **already GitOps** — ArgoCD app `longhorn-base` (`apps/workloads/longhorn-base.yaml` → `manifests/longhorn/`), auto-sync + prune + selfHeal + SSA. **Explicit `Setting` CRs = continuously enforced** (stronger than Helm `defaultSettings`, which only seeds at install). |
| Node config (`nodes.longhorn.io`, e.g. swift-mac `allowScheduling=false`) | **runtime CRs**, created by Longhorn per k8s node — shipped by neither chart nor manifest; stays live-only (out of scope for this migration, unaffected). |
| Version | 1.12.1 (manager + all 60 engines) |

## Target architecture — TWO apps, clean separation of concerns
Keep the split that already exists; add a Helm app for the core only.

```
apps/platform/longhorn.yaml          (NEW)  Helm chart "longhorn" @ targetRevision 1.12.1
   → core: manager DS, CSI, driver-deployer, instance-managers, CRDs, PriorityClass, StorageClasses
   → values: defaultSettings {} (DO NOT manage settings here — longhorn-base owns them)

apps/workloads/longhorn-base.yaml    (KEEP) the Setting CRs + recurring-jobs + pvc-labels + backup
   → remains the settings authority (continuously enforced Setting CRs)
```

**Why not fold settings into Helm `defaultSettings`?** `defaultSettings` writes a `longhorn-default-setting`
ConfigMap that longhorn-manager consults **only to initialise a setting still at its default** — it does
**not** continuously enforce. Our tuned values live as explicit `Setting` CRs (selfHeal'd by longhorn-base),
which is strictly better. So the Helm app ships `defaultSettings: {}` (or only the backup-target seed) and
**longhorn-base stays the single source of truth for settings.** Avoid listing any setting in both.

## The hard part — in-place ADOPTION without a data-plane blip (the whole risk)
ArgoCD must take ownership of the **already-running** core objects **without recreating them**. The
instance-manager pods carry the live volume engines for all 60 volumes — if any were deleted/recreated,
those volumes detach → outage. So:

- **Mechanism = ServerSideApply adoption** (`syncOptions: ServerSideApply=true`), same as longhorn-base.
  SSA adopts existing objects by field-manager takeover (`--force-conflicts` is how ArgoCD resolves the
  kubectl-owned `last-applied-configuration` fields). **No uninstall/reinstall ever** (Longhorn uninstall
  deletes volumes — hard no).
- **Version parity is mandatory:** chart `targetRevision` **== 1.12.1 exactly**, and the rendered images /
  CSI sidecar tags / RBAC must match live. Any delta = ArgoCD wants to change a running component.
- **The gate is a DIFF, not a sync:** create the app with **auto-sync OFF** (manual), run `argocd app diff`
  / a server-side dry-run, and **read every proposed change**. Proceed to sync **only if** the diff is
  additive / no-op (adoption) — specifically **zero** of: CRD `Replace`, DaemonSet/Deployment recreate,
  instance-manager pod changes, StorageClass field changes, Service/ClusterIP changes. If the diff is
  destructive, **do not sync** — reconcile values to match live and re-diff.
- **CRDs:** 25 large Longhorn CRDs → **SSA is required** (client-side apply would blow the 262144-byte
  `metadata.annotations` limit). Expect `ignoreDifferences` for webhook/conversion + defaulted fields; the
  chart's CRDs at 1.12.1 must equal the live CRDs (same version → should be identical; verify in the diff).

## Risk-gated cutover plan (the runbook, when scheduled)
1. **Preflight:** cluster healthy, 0 faulted/degraded/rebuilding; a fresh **Longhorn system backup** + the
   U0 CNPG recovery gate still green (same prerequisite as the climb — adoption is low-risk but data-plane
   objects are in play).
2. **Register the chart repo** in ArgoCD if absent (`https://charts.longhorn.io`, or mirror to the OCI
   registry per house pattern). Confirm `minicloud-platform` AppProject `clusterResourceWhitelist` allows
   `apiextensions.k8s.io/CustomResourceDefinition`, `scheduling.k8s.io/PriorityClass`,
   `storage.k8s.io/{StorageClass,CSIDriver}`, `rbac.authorization.k8s.io/*` (add if missing — PriorityClass
   whitelist is a known gotcha, see memory).
3. **Author `apps/platform/longhorn.yaml`** — Helm source, `targetRevision: 1.12.1`, `releaseName: longhorn`,
   namespace `longhorn-system`, `CreateNamespace=false`, `ServerSideApply=true`, **`syncPolicy.automated`
   ABSENT (manual)**, `defaultSettings: {}`. Values reconciled to match the live render (images, CSI, the
   `priorityClass`, `preUpgradeChecker` off, etc.).
4. **DIFF GATE (the go/no-go):** `argocd app diff longhorn` (or `kubectl apply --server-side --dry-run`).
   Iterate the values until the diff shows **only adoption/no-op**. This is the step that makes it safe.
5. **Sync once, watch the data plane:** sync; confirm manager/CSI pods are **adopted in place** (no
   restart), instance-managers untouched, **0 faulted** throughout, app `Synced/Healthy`. Smoke: a CNPG
   read/write, Vault unsealed, NATS JS.
6. **Enable auto-sync** (`automated: {prune: true, selfHeal: true}` + retry) **only after** a clean manual
   sync — same discipline as any new auto-sync app. **CODEOWNERS-gate** `apps/platform/longhorn.yaml`.
7. **Decommission the manual path:** mark `docs/longhorn-upstream/*.yaml` historical (keep for the record);
   update `reliability-longhorn-upgrade.md` + this doc to say the core is now Helm/ArgoCD-managed.

## Upgrades after migration (how Finding A is actually closed)
Future Longhorn upgrade = **bump `targetRevision` to the next minor** → CODEOWNERS PR → ArgoCD syncs the
manager/CSI rollout. **Longhorn's no-skip-minor rule still applies** (one minor per PR). The **engine
migration** (climb step: migrate all volume engines to the new version) is driven by the
`concurrent-automatic-engine-upgrade-per-node-limit` setting — set it to `1` as a **`Setting` CR in
longhorn-base** for the upgrade PR window, revert to `0` after (or leave a small value). The per-hop
**health gate** from the climb (0 faulted, engines reconciled, app smoke) stays the pre-merge/post-sync
check. Net: the climb's proven procedure, now expressed as PRs instead of manual `kubectl apply`.

## Rollback
Adoption is reversible because it changes *ownership*, not data: if a sync misbehaves, **delete the
`longhorn` ArgoCD app with `prune: false`** (leaves all objects running) and fall back to the raw manifest
(`kubectl apply -f docs/longhorn-upstream/longhorn-1.12.1.yaml`) to reclaim kubectl ownership. Volume data
is never touched by any step (no uninstall, no CRD delete, no instance-manager recreate — the diff gate
guarantees this before the first sync).

## Decisions & open questions (for the owner)
- **[Recommend] Keep the two-app split** (Helm core + longhorn-base settings) rather than folding settings
  into Helm values — explicit Setting CRs are continuously enforced; `defaultSettings` is not. *(Owner call;
  low-risk either way.)*
- **Chart delivery:** official `https://charts.longhorn.io` vs mirror to the house OCI registry. Recommend
  the OCI mirror if the repo-server can't reach the public chart repo (egress), else the public repo.
- **Timing:** low-urgency governance polish — schedule when convenient; no reliability driver. Fine to park.

## Effort / risk
- **Effort:** ~0.5–1 session (author the app + values, the diff-iteration is the real work).
- **Risk:** **low IF the diff gate is honoured** (adoption of a healthy system); **high if synced blind**
  (a destructive diff could recreate instance-managers → detach). The entire safety is in step 4.
- **Blast radius:** the storage layer for all 60 volumes → treat as Path B with the governance gate +
  CODEOWNERS; do it attended, not via auto-sync on first apply.
