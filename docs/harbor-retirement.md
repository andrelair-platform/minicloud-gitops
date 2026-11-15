# ADR — Retire Harbor; use ghcr for BOTH dev and prod

**Status:** Accepted (owner-approved 2026-11-15) · **Owner:** Platform Eng (SA/TL + DO) · **Board:** #3
(GitOps — Platform Engineering). Supersedes the **hybrid registry** model (dev→Harbor, prod→ghcr) in
`gitops.md` / `ci-registry.md`.

## Context
The platform ran a **hybrid container registry**: dev images → self-hosted **Harbor** (on-cluster,
Longhorn-backed), prod images → **ghcr.io** (free, durable, off-cluster). The stated rationale — "keep the
*controller* disk bounded" — was **weak**: Harbor runs on **Longhorn in-cluster**, not the controller, so
it never protected the controller; instead it **consumes the exact flaky storage layer that keeps
breaking**. Harbor is a heavy app (core + registry + its own Postgres + redis + jobservice + trivy +
portal) on a **resource-constrained, storage-flaky** 6-node cluster, and has been a **recurring incident +
toil source**: registry-flap-on-stale-RO-node, the `postgresql-noavx512` image GC'd out (6-day litellm
outage), the retention-config-re-apply-after-rebuild runbook, the `HARBOR_USER` repo-secret-shadowing CI
trap — and, on 2026-11-15, a `harbor-database` crashloop (triggered by a storage-node `ReadonlyFilesystem`
condition) took the Harbor API to 503 and **blocked all dev CI pushes**.

## Options
1. **Keep the hybrid model, recover each incident** — status quo; keeps the toil + the whole-dev-CI-blast-radius.
2. **ghcr-only for dev + prod (chosen)** — one registry, off-cluster, free, already proven for prod.
3. External managed registry (ECR/ACR) — cost + another cloud dependency; no gain over ghcr.

## Decision
**Retire Harbor. Use `ghcr.io/andrelair-platform/*` for BOTH dev and prod images.** The CI already
dual-pushes to ghcr on `main`; dev simply stops pushing/pulling Harbor and uses ghcr too.

## Trade-offs (honest)
- **Give up:** self-hosted **sovereignty** of the *image registry* (prod already depended on ghcr — the
  sovereign crown jewels are the **data** (CNPG/EU), not dev images); **offline-capability** of dev pulls
  (dev isn't what you need during an internet outage); and Harbor's **pull-through proxy cache**
  (docker-hub/quay/k8s + the `minio` mirror that dodged the docker.io anon-paywall).
- **Keep:** cosign signing + SBOM + Trivy (all already on the ghcr path); immutable SHA tags; the
  CODEOWNERS prod gate; Kargo promotion (now dev+prod on one registry → **cleaner dev/prod parity**).
- **Gain:** one registry, no Harbor pods/PVCs (reclaimed memory + less Longhorn replica churn — the thing
  that breaks), no hybrid-registry footguns (the ghcr-newName-on-prod-overlay rule, the retention runbook,
  the repo-secret shadow), and **no "Harbor down blocks all dev CI"**.

## Migration (big-bang, safe order)
1. **Migrate the Harbor-only *non-CI* images to ghcr** via a GitHub Actions `crane` workflow (uses the
   Actions `GITHUB_TOKEN` for ghcr write — no PAT needed; Tailscale + Harbor creds to read Harbor):
   `postgresql:18.4.0-noavx512` (used by `ai/postgresql-ai-0` + velero restore-drills), the `minio`
   mirror, `litellm-custom`, `mlflow-psycopg2`, `markitdown-proxy`. Then repoint their manifests to ghcr.
2. **Flip every CI-built service** (CI drops the Harbor dual-push → ghcr-only; dev values/overlays repoint
   `harbor.10.0.0.200.nip.io/library/<x>` → `ghcr.io/andrelair-platform/<x>`); ensure the `ghcr-pull`
   imagePullSecret (ESO ← Vault `platform/ghcr`) exists in each consuming namespace for private packages.
   Delete stale repo-level `HARBOR_*` secrets.
3. **Proxy-cache:** repoint the few pull-through consumers to upstream (accept the low rate-limit risk on a
   small cluster) and point `minio` at its ghcr-migrated copy.
4. **Decommission Harbor:** remove the ArgoCD app + manifests, reclaim the Longhorn PVCs, drop the
   `harbor.*` DNS/ingress, and remove the retention/GC runbooks.

## Consequences
- `gitops.md` / `ci-registry.md` / `ops-runbooks.md` updated: one registry (ghcr), no Harbor.
- A separate storage item remains: `loving-gannet` `ReadonlyFilesystem=True` (the stale-RO condition that
  wobbled Harbor's DB) — handled on the storage track, not here.
- Reference: this ADR + the per-service flip PRs + the `migrate-harbor-to-ghcr` Action.
