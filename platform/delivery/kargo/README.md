# Kargo — multi-stage promotion control plane

Kargo sits **on top of** Argo CD. Argo CD's job is "make the cluster match Git for
one environment." Kargo's job is the thing Argo CD does *not* do: **move a verified
artifact from stage to stage**, and write the Git commit/PR that Argo CD then
reconciles. It never touches the cluster directly — it only produces Git changes,
so our GitOps model (and the CODEOWNERS prod gate) stays intact.

- Install: `apps/platform/kargo.yaml` (Helm chart `oci://ghcr.io/akuity/kargo-charts/kargo`).
- Per-service pipelines: `services/<svc>/kargo/` — a `Project`, a `Warehouse`
  (watches the prod image repo), and two `Stage`s (`dev`, `prod`).
- UI: <https://kargo.10.0.0.200.nip.io> (Tailscale + minicloud CA).

## Promotion model (matches our 2-env, git-gated-prod standard)

```
Warehouse (watches ghcr prod image) ──► Freight (an immutable artifact set)
        │
   Stage: dev   promotionTemplate → bump dev overlay → open PR (auto-merge) → Argo syncs dev
        │  (freight must be live in dev before it can go to prod)
   Stage: prod  promotionTemplate → bump prod overlay → open **CODEOWNERS-gated PR** → review → Argo syncs prod
```

Every overlay change still lands via a PR against protected `main` — exactly like
today. Kargo just *opens* those PRs. The prod PR is the promotion gate (CODEOWNERS),
and the live canary Rollout + AnalysisTemplate remain the runtime safety brake.

## Safe-by-default posture (this spike)

- **No auto-promotion is configured.** Freight is discovered automatically, but a
  promotion only runs when you trigger it in the Kargo UI/CLI. So Kargo cannot
  fight the existing CI dev image-bump, and cannot open a prod PR on its own until
  you opt in. Nothing here changes a running deployment on merge.
- To cut a service fully over to Kargo later: enable auto-promotion for its `dev`
  Stage (a `ProjectConfig` `promotionPolicy`) and delete that service's CI
  `bump-gitops` step. The `automerge` auto-merge is already wired
  (`.github/workflows/kargo-automerge.yml` — merges dev-overlay-only PRs labelled
  `automerge`, refuses anything touching prod/base/apps).

## One-time bootstrap (before first login)

`secret/platform/kargo` is **pre-staged**: `token-signing-key` (generated),
`git-username` (`AndreLiar`) and `git-token` (copied from the existing
`GITOPS_TOKEN`) are already set. The `kargo-api` secret (admin hash + signing key)
is rendered from it by `admin-externalsecret.yaml`, and each service's
`git-credentials.yaml` renders the Git credential — nothing to wire by hand.

**Only one value is left for you: `admin-password-hash`** (your Kargo UI password).
Until it is set, admin login is disabled (the API waits — nothing leaks). Set it:

```bash
# bcrypt hash of your chosen admin password (never commit the plaintext):
HASH=$(htpasswd -bnBC 10 "" '<ADMIN_PASSWORD>' | tr -d ':\n' | sed 's/$2y/$2a/')
# patch it into the pre-staged Vault secret (root token from the controller):
VAULT_ROOT=$(ssh controller "cat ~/.vault-root-token")
vault kv patch secret/platform/kargo admin-password-hash="$HASH"   # or the KV v2 API
```

ESO refreshes `kargo-api` within its interval (or delete the ExternalSecret to force
an immediate re-render); the `kargo-api` pod then serves your login.

**ghcr read token (Internal images only)** is reused from `secret/platform/ghcr`
(`username`, `token`) by `image-credentials.yaml` for minicloud-plane / -agent /
-crew-agent. `platform-demo`'s ghcr package is Public → no image credential.

## Verify after install

```bash
kubectl -n kargo get pods
kubectl -n kargo get svc kargo-api -o jsonpath='{.spec.ports}'   # confirm ingress port
kubectl get warehouses,stages -A
```
