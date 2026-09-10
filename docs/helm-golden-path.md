# ADR: Helm library-chart golden path for custom apps

**Status:** Accepted (pilot pending) · **Date:** 2026-09-10 · **Board:** GitOps — Platform Engineering (#3)

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
