# minicloud — GitOps source-of-truth

ArgoCD watches this repo and reconciles the cluster against it. Every commit
that lands on `main` triggers a sync within ~3 minutes (the default ArgoCD
reconciliation interval).

**Live docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>
— see Phase 12 (ArgoCD/GitOps) and Phase 13 (CI/CD pipeline) for the
architectural reasoning.

**Sibling repos in the [andrelair-platform](https://github.com/andrelair-platform) org:**
[docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[ansible](https://github.com/andrelair-platform/minicloud-ansible) ·
[opentofu](https://github.com/andrelair-platform/minicloud-opentofu) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo)

## Layout

```
.
├── bootstrap/
│   └── root-app.yaml         # the app-of-apps root Application
├── apps/                     # one Application per child app
│   ├── homer.yaml            # → manifests/homer/   (migrated from raw kubectl)
│   └── whoami.yaml           # → manifests/whoami/  (greenfield ArgoCD-managed)
└── manifests/
    ├── homer/                # ConfigMap + Deployment + Service + Ingress + Namespace
    └── whoami/               # Deployment + Service + Ingress + Namespace
```

## Bootstrap

```bash
kubectl apply -f bootstrap/root-app.yaml
```

That single Application syncs the `apps/` directory. ArgoCD then creates
each child Application (`homer`, `whoami`) and reconciles their respective
`manifests/` paths.

## What's NOT here yet

Phase 12 only migrated **Homer** (low-risk, stateless) and added a new
`whoami` demo. Still helm-managed (intentionally — migrating these is a
later phase):

- `ingress-nginx` (critical-path)
- `metallb-system` (critical-path)
- `harbor` (stateful, 5 PVCs)
- `monitoring` (kube-prometheus-stack, 3 PVCs, complex CRDs)
- `podinfo` (Phase 9's HPA + custom dashboard test rig)

Each of those will get its own migration phase later, with downtime
considerations and a clean rollback plan.

## ArgoCD UI

`http://argocd.10.0.0.200.nip.io` — admin password in `~/.argocd-admin`
(mode 600, never committed) on the controller.
