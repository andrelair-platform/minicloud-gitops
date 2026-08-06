# GitOps & Backstage

## GitOps Service Structure (Kustomize)

Own services use Kustomize base + minicloud-1/{env} overlays in `minicloud-gitops/services/`.
**All Helm values live in `minicloud-gitops/helm-values/minicloud-1/`** — never edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools.

```
minicloud-gitops/services/<service>/
├── base/                          # no namespace, no image tag
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── minicloud-1/               # cluster dimension
    ├── dev/                       # auto-sync, CI updates newTag here
    ├── staging/                   # manual sync, PR to promote
    └── prod/                      # manual sync, ingress+cert here
```

**ArgoCD apps split:** `apps/platform/` (43 infra apps) + `apps/workloads/` (28 services). Root-app has `recurse: true`.

**Promotion flow:** CI → `kustomize edit set image` in `minicloud-1/dev/` only. Staging and prod require explicit PRs.

**New service checklist:**
1. Copy `services/_template/` and replace `SERVICE_NAME`
2. Add namespaces to AppProject `manifests/argocd-project/00-project.yaml`
3. Add ArgoCD Application files in `apps/`
4. Update Vault Kubernetes auth role
5. Add `minicloud-1/prod/ingress.yaml` + `certificate.yaml` for public URL

```bash
cd ~/Developer/cloudplateform/minicloud-gitops
kustomize build services/platform-demo/minicloud-1/dev
```

## Backstage Custom Image

Source at `~/Developer/cloudplateform/minicloud-backstage`. CI is fully automated.

**CRITICAL — production config is NOT in minicloud-backstage:**
`app-config.yaml` in that repo is local dev only. Production config comes from ConfigMap `backstage-app-config` rendered from `minicloud-gitops/helm-values/minicloud-1/backstage-values.yaml` (`appConfig` section). To add catalog locations, proxy endpoints, or any prod config → edit that values file, push, then `kubectl rollout restart deployment/backstage -n backstage`.

```bash
cd ~/Developer/cloudplateform/minicloud-backstage
yarn install --immutable && yarn tsc && yarn build:backend
```
