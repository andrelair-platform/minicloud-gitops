# minicloud-gitops — GitOps source-of-truth

ArgoCD app-of-apps source for the minicloud enterprise Kubernetes platform.
Every commit to `main` triggers a cluster reconciliation within ~3 minutes (default ArgoCD reconciliation interval).

**Live docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>  
**Portfolio:** <https://www.devandre.sbs>

**Sibling repos in the [andrelair-platform](https://github.com/andrelair-platform) org:**  
[docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[ansible](https://github.com/andrelair-platform/minicloud-ansible) ·
[litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) ·
[rag-ingest](https://github.com/andrelair-platform/minicloud-rag-ingest) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo)

---

## What this repo is

Single source of truth for all cluster state. ArgoCD watches `apps/` and reconciles 54+ workloads.
No `kubectl apply` ever runs manually against the cluster for managed workloads — git is the only write path.

**Rule:** if it runs in the cluster, it has a manifest or Helm values file here.

---

## Layout

```
.
├── bootstrap/
│   └── root-app.yaml              # one-time apply — creates the app-of-apps root Application
├── apps/                          # one Application YAML per workload (54+ apps)
│   ├── litellm.yaml               # Enterprise AI Gateway (multi-source Helm)
│   ├── langfuse.yaml              # Langfuse LLMOps + ClickHouse + Valkey
│   ├── ollama.yaml / ollama-secondary.yaml / ollama-tertiary.yaml
│   ├── open-webui.yaml
│   ├── vault.yaml                 # HashiCorp Vault (AWS KMS auto-unseal)
│   ├── kube-prometheus-stack.yaml # Prometheus + Grafana + Alertmanager
│   └── ...
├── helm-values/                   # all Helm values files (canonical — never edit ansible/helm-values/)
│   ├── litellm-values.yaml
│   ├── kube-prometheus-stack-values.yaml
│   ├── vault-values.yaml
│   └── ...
├── manifests/                     # raw Kubernetes manifests
│   ├── ai/                        # LiteLLM configmap, Langfuse, RAG services, Grafana dashboard
│   ├── argocd-project/            # AppProject — locked sourceRepos + clusterResourceWhitelist
│   ├── eso-platform-secrets/      # 13 ExternalSecrets pulling from Vault KV
│   ├── network-policies/          # default-deny + explicit allow rules across 23 namespaces
│   ├── quotas/                    # ResourceQuota + LimitRange per namespace
│   └── gatekeeper-policies/       # 9 OPA ConstraintTemplates + Constraints (all deny mode)
├── services/                      # Kustomize base+overlays for internal services
│   ├── platform-demo/             # Go CI/CD demo (base + dev/staging/prod overlays)
│   └── _template/                 # scaffold for new services
└── docs/
    └── ai-gateway/
        └── dept-key-governance.md # department key allowlist details
```

---

## Bootstrap

```bash
# One-time only — apply the root app, ArgoCD creates all child apps from apps/
kubectl apply -f bootstrap/root-app.yaml
```

After that, every change goes through git. ArgoCD auto-syncs within ~3 minutes.

---

## Platform at a Glance

| Check | Status |
|---|---|
| ArgoCD apps synced | 54 / 54 |
| OPA Gatekeeper policies (deny mode) | 9 / 9 — 0 violations |
| Regression checks | 62 PASS / 0 FAIL / 0 WARN |
| Zero-trust NetworkPolicy namespaces | 23 / 23 |
| ESO ExternalSecrets synced | 13 / 13 |
| TLS certificates ready | 20 / 20 |

---

## Key Rules

**Helm values:** all values live in `helm-values/`. Do NOT edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools — ArgoCD reads from here only.

**New service checklist:**
1. Copy `services/_template/` and replace `SERVICE_NAME`
2. Add namespace to AppProject `manifests/argocd-project/00-project.yaml`
3. Add ArgoCD Application in `apps/`
4. Add Vault Kubernetes auth role for `<service>-dev` + `<service>-staging`
5. Add `overlays/prod/ingress.yaml` + `certificate.yaml` for public URL

**AI Gateway config:** edit in [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) — CI syncs `config/litellm-config.yaml` into `manifests/ai/00-litellm-configmap.yaml`. Never edit that file directly here.

**Webhook namespaces** (cert-manager, external-secrets, gatekeeper-system, keda, vault): NetworkPolicy `allow-webhook-from-apiserver` must include both `10.0.0.0/24` (control plane) and `10.42.0.0/24` (flannel VTEP for worker nodes).
