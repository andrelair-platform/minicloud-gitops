# ADR — PR Preview Environments (ephemeral, opt-in, scoped to platform-demo)

- **Status:** Proposed — design recorded; the existing implementation is **built-but-broken** (see §4) and needs the §5 fix before it works.
- **Date:** 2026-10-17
- **Deciders:** Platform Engineering (@AndreLair)
- **Scope:** `platform-demo` only (the reference/demo service), as a deliberately bounded pilot.

## 1. Context — why previews, and why *bounded*

A per-PR **ephemeral environment** (spin up the PR's code at a real URL, tear it down on merge/close)
is a strong delivery signal — reviewers test behaviour, not just diffs. But on a **5-node, tight-quota**
cluster with a **need-first** constitution, an *unbounded* preview system (one running env per open PR)
is a real resource + maintenance liability. `platform-demo` alone has **>10 open PRs** at any time
(mostly Renovate dep-bumps) — auto-previewing all of them would be a standing waste.

What already exists and partially covers the need:
- **`pr-manifest-diff.yml`** — renders the real rendered-manifest diff on every GitOps PR (a *config*
  preview).
- The **dev environment** (Kargo-fed from `main`) — a living, always-on environment.

So previews are **additive polish**, not a gap in the core flow. The design below is therefore
**opt-in and single-service**, not a platform-wide PR-preview factory.

## 2. Decision

Provide ephemeral preview environments **only when a PR is explicitly labelled `preview`**, **only for
`platform-demo`**, via the **CI-push model** (app CI writes an ArgoCD `Application` into
`minicloud-gitops/apps/previews/`; the recursing root app deploys it; an ArgoCD finalizer prunes the
namespace on teardown). Keep it within the Helm golden path and a per-namespace resource quota.

**Opt-in by label is the keystone decision** — it bounds blast radius to the handful of PRs a human
chooses, so Renovate/dependabot noise never spins up compute.

## 3. As-built design (what the CI-push model does)

`platform-demo/.github/workflows/preview.yml` (already present):

```
PR labelled `preview` (or synchronize while labelled)
  → build image  harbor…/library/platform-demo:pr-<n>-<sha>
  → write apps/previews/preview-pd-<n>.yaml  (an ArgoCD Application → ns preview-pd-<n>)
  → open + merge a gitops PR            (root-app recurse:true discovers it, syncs ~30s)
PR unlabelled `preview` / closed
  → delete apps/previews/preview-pd-<n>.yaml
  → the Application's `resources-finalizer.argocd.argoproj.io` prunes the namespace + all resources
```

Chosen deliberately over an **ApplicationSet PR generator** because the CI-push model needs **no GitHub
token wired into the ArgoCD ApplicationSet controller** and keeps the trigger logic (label gating, image
build) in the app's own CI.

## 4. Current state — BROKEN (do not enable as-is)

Two defects make the as-built workflow fail if triggered today:

1. **Stale kustomize path (post-Helm-migration).** The generated Application points at
   `services/platform-demo/minicloud-1/preview` with a `kustomize.images` override. That path **was
   deleted** when the repo went **Helm-only** (2026-09-24 — zero `kustomization.yaml`). ArgoCD would
   report `ComparisonError: app path does not exist`. The preview predates the golden path.

2. **Vault agent injection in a dynamic namespace.** `platform-demo`'s pod uses **Vault agent
   injection** (`vault.hashicorp.com/role: platform-demo`). Vault's k8s-auth role binds **fixed**
   namespaces (`platform-demo`, `platform-demo-dev`). A per-PR `preview-pd-<n>` namespace is **not
   bound** → the injector denies the pod (`permission denied` / missing SA mount) → the preview never
   starts.

## 5. Required fix (the real work — port to the Helm golden path)

1. **`services/platform-demo/helm/values-preview.yaml`** — a preview overlay that:
   - targets the Helm wrapper chart (`path: services/platform-demo/helm`, `releaseName: preview-pd-<n>`);
   - **disables Vault agent injection** and supplies the app's config via the `appConfig` ConfigMap with
     **dummy preview values** (a preview needs *a* config, not the real secret) — this resolves defect #2;
   - sets `automountServiceAccountToken: false` (Vault off → hardened default restored);
   - **replicas: 1, KEDA scale-to-zero disabled** (a preview must be reachable without the interceptor
     dance), simple rollout (no canary gate);
   - per-PR **image tag + ingress host + TLS dnsName** injected by the generated Application via
     `helm.valuesObject` (`pd-pr-<n>.10.0.0.200.nip.io`, `tag: pr-<n>-<sha>`).
2. **Rewrite `preview.yml`'s Application generation** to emit the Helm source above (drop the dead
   kustomize block) — resolves defect #1.
3. **Resource bound** — a small `ResourceQuota` + `LimitRange` applied to each `preview-pd-<n>` namespace
   (templated in the preview overlay), so a preview can never exceed a fixed CPU/mem envelope.
4. **Verify live** — label a throwaway PR `preview` → confirm build → Application synced → pod Ready → URL
   `200` → unlabel → namespace pruned. *A preview env is not "done" until this round-trip is proven.*

## 6. Trade-offs & open questions

- **`--admin` CODEOWNERS bypass.** `preview.yml` opens a gitops PR and `gh pr merge --admin` it, because
  `apps/` is CODEOWNERS-gated and an ephemeral preview can't wait for human review. This is a *deliberate,
  scoped* hole: the token can admin-merge **preview Applications only** (the branch/paths are
  `preview/pd-*` → `apps/previews/`). **Recommendation:** narrow it further by excluding `apps/previews/`
  from the CODEOWNERS gate and merging via the normal `automerge` path, so no `--admin` is needed — or
  accept the bypass as scoped and documented. Not yet decided.
- **Cost.** One preview ≈ 1 replica + a small DB-less footprint; bounded by the per-ns quota and by the
  opt-in label. No scale-to-zero (reachability > thrift for a short-lived preview).
- **Security.** Previews run the same Gatekeeper-restricted, SSO-gated posture as any workload; the dummy
  config carries no real secret (Vault is off for previews).

## 7. When to (actually) build / enable it

Enable the §5 fix when previews earn their keep — e.g. when a human reviewer repeatedly wants to click a
running PR build. Until then this ADR is the plan; `pr-manifest-diff` + the dev env cover the day-to-day.
**Do not** generalise to an all-services ApplicationSet PR factory on this cluster without the resource
headroom and the per-PR image builds to match (need-first).

## Related

- `gitops.md` (Helm golden path · Kargo · CODEOWNERS gate) · `conventions.md` (deploy-repo rule) ·
  `.github/workflows/pr-manifest-diff.yml` (the config-preview that already exists) ·
  `docs/helm-golden-path.md`.
