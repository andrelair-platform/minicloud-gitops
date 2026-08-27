# GitOps & Backstage

## GitOps Service Structure (Kustomize)

Own services use Kustomize base + minicloud-1/{env} overlays in `minicloud-gitops/services/`.
**All Helm values live in `minicloud-gitops/helm-values/minicloud-1/`** — never edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools.

**The default is 2 environments: `dev` + `prod`.** dev = 1 replica (auto-sync), prod = 2–3 replicas (manual sync). Staging is **opt-in** — only for services that need a third gate (currently `ktayl-policy-service`/CERT-1 and `platform-demo`). Resource-constrained cluster → don't scaffold staging by default.

```
minicloud-gitops/services/<service>/
├── base/                          # no namespace, no image tag; replicas: 1
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── minicloud-1/               # cluster dimension
    ├── dev/                       # auto-sync, CI updates newTag; replicas 1 (base)
    └── prod/                      # manual sync, ingress+cert; patch-replicas → 2–3
        # staging/ is opt-in — see services/_template/minicloud-1/_staging-optional/README.md
```

**ArgoCD apps split:** `apps/platform/` (43 infra apps) + `apps/workloads/` services. Root-app has `recurse: true`.

**Promotion flow (2-env default):** CI → `kustomize edit set image` in `minicloud-1/dev/` only → `dev (auto) → prod (PR)`. With opt-in staging: `dev (auto) → staging (PR) → prod (PR)`. prod always requires an explicit PR + manual sync.

**Prod HA:** give each prod overlay a `patch-replicas.yaml` (`replicas: 2`, up to 3) targeting the Deployment/Rollout — dev inherits base `replicas: 1`. Only skip for singletons (RWO PVC / stateful). Reference: minicloud-plane (Rollout), minicloud-agent + minicloud-crew-agent (Deployment).

**New service checklist:**
1. Copy `services/_template/` and replace `SERVICE_NAME` (template ships dev+prod; staging lives under `_staging-optional/`)
2. Add namespaces to AppProject `manifests/argocd-project/00-project.yaml`
3. Add ArgoCD Application files in `apps/` (dev auto-sync, prod manual)
4. Update Vault Kubernetes auth role
5. Add `minicloud-1/prod/ingress.yaml` + `certificate.yaml` for public URL
6. To add staging later: follow `services/_template/minicloud-1/_staging-optional/README.md`

```bash
cd ~/Developer/cloudplateform/minicloud-gitops
kustomize build services/platform-demo/minicloud-1/dev
```

## ESO + ArgoCD SSA ignoreDifferences (mandatory for any ExternalSecret)

When an Application uses `ServerSideApply=true` and contains an `ExternalSecret`, ESO's admission webhook injects four default fields at creation time that are never in git: `conversionStrategy: Default`, `decodingStrategy: None`, `metadataPolicy: None`, `deletionPolicy: Retain`. ArgoCD SSA diff sees these as drift → app is permanently `OutOfSync` (even though pods are Healthy and the secret is synced).

**Fix — add to every Application that contains an ExternalSecret:**

```yaml
ignoreDifferences:
  - group: external-secrets.io
    kind: ExternalSecret
    jqPathExpressions:
      - .spec.data[].remoteRef.conversionStrategy
      - .spec.data[].remoteRef.decodingStrategy
      - .spec.data[].remoteRef.metadataPolicy
      - .spec.target.deletionPolicy
syncOptions:
  - RespectIgnoreDifferences=true   # must be here alongside CreateNamespace/ServerSideApply
```

`RespectIgnoreDifferences=true` is required — without it ArgoCD still overwrites the ignored fields on each sync, causing ESO to re-inject them in an endless loop.

Reference: PRs #729 (minicloud-agent-dev + minicloud-crew-agent-dev fix).

## Backstage Custom Image

Source at `~/Developer/cloudplateform/minicloud-backstage`. CI is fully automated.

**CRITICAL — production config is NOT in minicloud-backstage:**
`app-config.yaml` in that repo is local dev only. Production config comes from ConfigMap `backstage-app-config` rendered from `minicloud-gitops/helm-values/minicloud-1/backstage-values.yaml` (`appConfig` section). To add catalog locations, proxy endpoints, or any prod config → edit that values file, push, then `kubectl rollout restart deployment/backstage -n backstage`.

```bash
cd ~/Developer/cloudplateform/minicloud-backstage
yarn install --immutable && yarn tsc && yarn build:backend
```
