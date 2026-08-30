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

1. **Admin credentials** — generate a bcrypt password hash + a random token signing
   key and store them in Vault, then set them on the chart values (or patch the
   `kargo-api` secret):

   ```bash
   # bcrypt hash of your chosen admin password:
   htpasswd -bnBC 10 "" '<ADMIN_PASSWORD>' | tr -d ':\n' | sed 's/$2y/$2a/'
   # random signing key:
   openssl rand -base64 48
   # store both in Vault (root token from the controller):
   #   secret/platform/kargo  ->  admin-password-hash, token-signing-key,
   #                              git-username, git-token
   ```

   Put `admin-password-hash` and `token-signing-key` into
   `apps/platform/kargo.yaml` `api.adminAccount.passwordHash/tokenSigningKey`
   (the hash is safe to commit; keep the signing key out of git by patching the
   `kargo-api` secret instead if you prefer).

2. **Git PAT for opening PRs** — a fine-grained PAT on `andrelair-platform/minicloud-gitops`
   with `contents:write` + `pull_requests:write`. Store as `git-username` (the bot
   login) + `git-token` in Vault `secret/platform/kargo`. Each service's
   `services/<svc>/kargo/git-credentials.yaml` ExternalSecret renders it into the
   project namespace as a Kargo `git` credential.

3. **ghcr read token (Internal images only)** — reuse `secret/platform/ghcr`
   (`username`, `token`, `read:packages`). Rendered per project namespace by
   `image-credentials.yaml` where the prod image package is Internal
   (minicloud-plane / minicloud-agent / minicloud-crew-agent / retrieva).
   `platform-demo`'s ghcr package is Public → no image credential.

## Verify after install

```bash
kubectl -n kargo get pods
kubectl -n kargo get svc kargo-api -o jsonpath='{.spec.ports}'   # confirm ingress port
kubectl get warehouses,stages -A
```
