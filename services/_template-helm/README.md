# _template-helm — golden-path scaffold for a custom app

Copy this for a NEW custom service, replace `SERVICE_NAME`, and you have a full app on the
minicloud-app-deployment library chart. A service = **3 values files + 2 ArgoCD Applications**.
See `docs/helm-golden-path.md` (ADR) for the model and the migration checklist below.

## Onboard / migrate checklist (the 5 gotchas the ktayl-policy pilot surfaced)
1. **AppProject sourceRepos** already allows `harbor.10.0.0.200.nip.io/library` + `ghcr.io/andrelair-platform` (done once).
2. **NetworkPolicies** — if the ns has policies selecting `app: <name>`, keep `podLabels: {app: <name>}` (values.yaml) so the chart pod matches them.
3. **Certificate** — do NOT enable the chart Certificate if the service already owns one; keep the cert as a satellite manifest (single owner + renewal). `certificate.enabled: false`.
4. **cert-manager issuer** (if you DO use the chart cert) = `minicloud-ca` (ClusterIssuer), not `minicloud-ca-issuer`.
5. **Migrating an existing service** — the Deployment selector changes (`app:` → `app.kubernetes.io/*`, immutable), so **delete the old Deployment once** on the flip; keep the old kustomize overlay until verified (rollback = repoint the Application source).

## Satellite resources
The chart renders the **workload** (Deployment/Rollout + Service/Ingress/KEDA/PDB/ServiceMonitor/ESO).
A service's **infra dependencies** (dedicated DB, extra ESO secrets, KEDA-HTTP interceptor, its
Certificate) stay as **adjacent manifests** referenced by the app — the chart is the workload golden
path, not the whole footprint.

## Chart publish (maintainers)
`helm package charts/minicloud-app-deployment` → `helm push` to `oci://harbor.../library` (dev) and
`oci://ghcr.io/andrelair-platform` (prod). Bump `Chart.yaml` version; update `targetRevision` in the apps.
