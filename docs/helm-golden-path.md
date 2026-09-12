# ADR: Helm library-chart golden path for custom apps

**Status:** Accepted · **Date:** 2026-09-10 (rev 2026-09-12) · **Board:** GitOps — Platform Engineering (#3)

> **Update 2026-09-12 — consumption model is the GAP WRAPPER CHART (not ArgoCD multi-source).**
> The *decision* below stands (one shared `minicloud-app-deployment` library chart). What changed is
> HOW an app consumes it: each app is **its own thin Helm chart** whose `Chart.yaml` declares a
> `dependencies:` on the library chart (pulled from ghcr OCI), configures it under the
> `minicloud-app-deployment:` values key, and carries its service-specific extras in its **own
> `templates/`**. The ArgoCD app is a **single Helm source** (`helm dependency build` resolves the OCI
> dep via the `ghcr-oci-repo` cred; `Chart.lock` committed). This supersedes the earlier **multi-source
> + `$values` + separate satellites** shape — it is pure Helm, locally renderable, and matches HDI's
> GAP model (sample: `deployment-acc082-french-ai-poc`). Converted: platform-demo, minicloud-agent,
> minicloud-crew-agent, minicloud-plane, ktayl-policy-service. Operational rules + gotchas
> (Chart.lock, `releaseName`, `.helmignore` no-`charts/`, `{{ }}` escaping, `selectorLabels` in-place
> flip) live in `.claude/rules/gitops.md`. **retrieva** is the last un-migrated app (dual-workload →
> two aliased library subchart deps; pair with its RTV-45 Mongo→PostgreSQL change).

## Context
Custom services used **Kustomize** (base + overlays); third-party apps use **Helm**. Two paradigms.
A shared, reusable golden path is awkward in Kustomize (patch-based, template-free). The HDI
Application Platform proves the better pattern: **one shared Helm chart + a thin per-app values file**.

## Decision
Adopt **`minicloud-app-deployment`** — a single versioned Helm chart that renders a hardened
Deployment/Rollout + Service + optional Ingress/Certificate + KEDA/HPA + egress NetworkPolicy + PDB +
ServiceMonitor + ESO ExternalSecret, entirely from values. Custom apps become **just a values file +
two ArgoCD Applications**. Third-party apps keep their upstream charts. One tool (Helm), one golden path.

### Distribution — hybrid registry (matches the image standard)
The chart is **dual-published as an OCI Helm chart**, exactly like images:
- **dev →** `oci://harbor.10.0.0.200.nip.io/library/minicloud-app-deployment:<ver>`
- **prod →** `oci://ghcr.io/andrelair-platform/minicloud-app-deployment:<ver>`
Source of truth: `charts/minicloud-app-deployment/` (SemVer in `Chart.yaml`).

### ArgoCD — multi-source
Each service has two Applications; each uses **source 1 = the OCI chart** (Harbor for `-dev`, ghcr for
`-prod`) + **source 2 = the gitops repo** supplying `services/<svc>/helm/values.yaml` +
`values-dev.yaml` / `values-prod.yaml` via `$values`. ArgoCD renders `helm template` (no Tiller/release
state). This per-env OCI split is how dev=Harbor / prod=ghcr is achieved for the same chart.

### Kargo, gate, envs
- **Kargo** promotion changes only its image-bump step: `kustomize edit set image` → a `yaml-update`
  that sets `.image.tag` in `values-dev.yaml` / `values-prod.yaml`. All else (dev auto-promote, prod
  CODEOWNERS PR, squash, verification) unchanged. Env-agnostic image + immutable SHA tag still required.
- **Prod gate (CODEOWNERS):** `services/*/helm/values-prod.yaml`, `charts/minicloud-app-deployment/**`
  (a chart change → new version → all-prod blast radius → must be gated), `apps/`, `manifests/kargo/`.
- **Envs:** exactly **dev + prod on the same cluster** (different namespaces). No uat, no multi-cluster —
  the HDI dev/uat/prod × region depth is flattened to `values-dev.yaml` / `values-prod.yaml`.

## The chart's config surface (hardened defaults)
`workload.kind: Deployment|Rollout` (Rollout = Argo canary/blueGreen, for plane/retrieva) · image ·
ports · probes · resources (limits mandatory) · env/envFrom · ingress+cert · scaledObject(KEDA)|hpa ·
networkPolicy (default DNS-only egress + allowlist) · pdb · serviceMonitor · externalSecret ·
`imagePullSecrets` · writableDirs (emptyDir for readOnlyRootFS). Secure-by-default: runAsNonRoot,
readOnlyRootFilesystem, seccomp RuntimeDefault, drop ALL caps.

## Rollout (no big-bang)
1. Build the chart (done, validated with `helm template`/`lint`). 2. **Pilot platform-demo** end-to-end
(OCI publish → ArgoCD multi-source → Kargo yaml-update → prod gate → KEDA). 3. Migrate plane (Rollout),
agent+crew (ghcr-pull+ESO), ktayl-policy, then **retrieva last** (git Warehouse, 2 images). Keep each
service's Kustomize overlays until its Helm cutover is verified; rollback = point the Application back
at the overlay.

## Consequences
- One paradigm; a service = a values file. Mirrors the HDI enterprise standard (portfolio/RNCP value).
- New maintained artifact = the library chart (blast radius managed by CODEOWNERS + gradual rollout +
  per-app canary brake).
- Third-party charts unchanged; single-env custom images (backstage/webui/onlyoffice/erpnext/ktayl-web)
  deferred.


## Migration gotcha: label-matched NetworkPolicies (root-caused in the ktayl-policy pilot)
The chart labels pods with `app.kubernetes.io/*`, but a service's **satellite NetworkPolicies** are
hand-written selecting the legacy **`app: <name>`** label (e.g. ktayl ns: `default-deny-egress` +
`allow-egress-postgres/nats/minio/jwks` all select `app: ktayl-policy-service`). A chart pod without
that label does NOT match the egress-allow rules → its DB/infra egress is denied → the app exits at
startup (observed: **exit 2, no logs** — it dies on the DB connect; DNS still works via a select-all
`allow-dns-egress`, which is why it gets that far). Pod spec is otherwise byte-identical to the overlay.

**Fix (per migrating service):** add a compatibility label via values `podLabels: {app: <name>}` so the
existing netpols keep matching — OR update that service's netpols to select `app.kubernetes.io/name`.
The `podLabels` route is least-churn for migration. **Every custom service migrating to the chart has
per-service netpols keyed on `app:` — apply this to each (plane/agent/crew/retrieva) before the flip.**


## Zero-downtime migration: `selectorLabels` override (chart 0.1.4, the no-delete flip)
A Deployment's `.spec.selector` is **immutable**. The chart's default selector is `app.kubernetes.io/*`,
but a service migrating off a kustomize overlay has an existing Deployment selecting the legacy
`app: <name>`. Two ways to reconcile that:

1. **Delete-first (dev, low-stakes):** `kubectl delete deploy <name>` once, then let ArgoCD recreate it
   with the chart's standard selector. Simple, but it **deletes the workload = brief downtime** — fine
   for a dev env, wrong for prod. (This is what the dev pilots + agent/crew prod used before 0.1.4.)
2. **`selectorLabels` override (prod, zero-downtime — chart 0.1.4):** set values
   `selectorLabels: {app: <name>}` so the chart renders a selector **identical** to the live
   Deployment's. ArgoCD then does an **in-place rolling update** (not a delete/recreate): the selector
   is unchanged, only the pod template changes → new ReplicaSet rolls in behind the Service + PDB with
   **no delete and no downtime**. The override label also lands on the pod, so it doubles as the netpol
   compatibility label — **use `selectorLabels`, NOT `podLabels`, on the migrating env** (setting both
   to `{app: <name>}` renders a duplicate map key). Note `app.kubernetes.io/*` is then absent from the
   pod, so any `podAntiAffinity`/ServiceMonitor selector must also target `app: <name>` in that env.

**This is strictly better than ArgoCD `Replace=true`** for the migration: `Replace=true` uses
`kubectl replace` = delete+recreate the Deployment = the same downtime as delete-first, just automated.
`selectorLabels` matching avoids the recreate entirely. Reference: **ktayl-policy prod** (HGP-10) — flip
verified in-place with the dedicated Postgres StatefulSet kept as an un-pruned satellite (identical
immutable spec → also in-place, data preserved).

Also delete the old Deployment once on a **delete-first** dev flip (immutable selector:
`app:` → `app.kubernetes.io/*`); a **prod** flip uses `selectorLabels` and needs no delete.
