# minicloud-gitops — GitOps source-of-truth

ArgoCD app-of-apps source for the minicloud enterprise Kubernetes platform. Every commit to `main` triggers an instant cluster reconciliation via the ArgoCD webhook.

**Live docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>  
**Portfolio:** <https://www.devandre.sbs>

**Sibling repos in the [andrelair-platform](https://github.com/andrelair-platform) org:**  
[backstage](https://github.com/andrelair-platform/minicloud-backstage) ·
[docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[ansible](https://github.com/andrelair-platform/minicloud-ansible) ·
[litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) ·
[rag-ingest](https://github.com/andrelair-platform/minicloud-rag-ingest) ·
[markitdown-proxy](https://github.com/andrelair-platform/minicloud-markitdown-proxy) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo)

---

## What this repo is

Single source of truth for all cluster state. ArgoCD watches `apps/` and reconciles 51 workloads automatically. No `kubectl apply` ever runs manually against the cluster for managed workloads — git is the only write path.

**Rule:** if it runs in the cluster, its manifest or Helm values file lives here.

---

## Platform at a Glance

| Check | Status |
|---|---|
| ArgoCD apps | 56 total — all Synced + Healthy |
| OPA Gatekeeper policies (deny mode) | 9 / 9 — 0 violations |
| Regression checks | 62 PASS / 0 FAIL / 0 WARN |
| Zero-trust NetworkPolicy namespaces | 23 / 23 |
| ESO ExternalSecrets synced | 14 / 14 |
| TLS certificates ready | 20 / 20 |

---

## Layout

```
.
├── bootstrap/
│   └── root-app.yaml              # one-time apply — creates the app-of-apps root Application
├── apps/                          # one Application YAML per workload (51 files)
│   ├── litellm.yaml               # Enterprise AI Gateway (multi-provider routing)
│   ├── langfuse.yaml              # Langfuse LLMOps + ClickHouse + Valkey
│   ├── ollama.yaml / ollama-secondary.yaml / ollama-tertiary.yaml
│   ├── open-webui.yaml            # Chat UI + RAG + BM25 French + cross-encoder re-ranker
│   ├── vault.yaml                 # HashiCorp Vault (AWS KMS auto-unseal)
│   ├── kube-prometheus-stack.yaml # Prometheus + Grafana + Alertmanager
│   ├── backstage.yaml             # Internal developer portal
│   ├── environments.yaml          # ApplicationSet: insurance/collab × dev/staging/prod
│   └── ...
├── helm-values/                   # all Helm values files (canonical — never edit ansible/helm-values/)
│   ├── litellm-values.yaml
│   ├── open-webui-values.yaml
│   ├── backstage-values.yaml      # bumped automatically by minicloud-backstage CI
│   ├── kube-prometheus-stack-values.yaml
│   └── ...
├── manifests/                     # raw Kubernetes manifests (grouped by concern)
│   ├── ai/                        # LiteLLM, RAG pipeline services, Docling, eval jobs
│   ├── argocd-project/            # AppProject — locked sourceRepos + clusterResourceWhitelist
│   ├── eso-platform-secrets/      # 14 ExternalSecrets pulling credentials from Vault KV
│   ├── gatekeeper-policies/       # 9 ConstraintTemplates + 9 Constraints (all deny mode)
│   ├── network-policies/          # default-deny ingress + explicit allow rules (23 namespaces)
│   ├── quotas/                    # ResourceQuota + LimitRange per namespace
│   └── rbac/                      # ClusterRoleBindings + accepted-risks documentation
├── services/                      # Kustomize base+overlays for internal services
│   ├── platform-demo/             # Go CI/CD demo (base + dev/staging/prod overlays)
│   └── _template/                 # scaffold — copy this for new services
└── tech-radar.json                # 39-entry Tech Radar data (read live by Backstage)
```

---

## Bootstrap

```bash
# One-time only — apply the root app; ArgoCD creates all child apps automatically
kubectl apply -f bootstrap/root-app.yaml
```

All subsequent changes go through git. ArgoCD syncs on every push via webhook.

---

## AI Platform

The AI stack lives in the `ai` namespace and is fully managed here.

| Component | Description |
|---|---|
| **LiteLLM** | AI Gateway: Groq, OpenAI, Gemini, DeepSeek, Mistral, Anthropic, HuggingFace, Ollama (local) |
| **Ollama** × 3 | Primary + secondary (fast-heron, 7 models each) + tertiary (fast-skunk, light models) |
| **Open WebUI** | Chat interface with RAG, SearXNG web search, BM25 French + HNSW hybrid retrieval |
| **Langfuse** | LLM observability — traces, scores, cost per department key |
| **Presidio** | PII/DLP guardrail (DATE_TIME/LOCATION excluded to avoid masking financial values) |
| **markitdown-proxy** | Document converter: PDF/images → Docling, Office → MarkItDown |
| **rag-ingest** | Ingest pipeline: convert → French-aware chunking → bge-m3 embed → pgvector INSERT |
| **postgresql-ai** | pgvector (1024-dim HNSW + GIN French FTS) for RAG; LiteLLM + Langfuse DBs |
| **phi3-financial** | Ollama model (FROM phi3.5 + financial system prompt) — local-only, never cloud-routed |

### AI Gateway config

LiteLLM config is managed in [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom). CI syncs `config/litellm-config.yaml` into `manifests/ai/00-litellm-configmap.yaml` automatically. **Do not edit that file directly here.**

### RAG eval pipeline

`manifests/ai/16-rag-eval-job.yaml` — ArgoCD PostSync hook that runs Ragas (GPT-4o judge) + ROUGE-L / Hit Rate / MRR after every `ai` namespace sync.  
`manifests/ai/17-rag-eval-cronjob.yaml` — 5% online sampling every 15 min with scores written back to Langfuse.

---

## Security Hardening

| Control | Detail |
|---|---|
| **NetworkPolicy** | Default-deny ingress on all 23 namespaces; webhook namespaces allow both `10.0.0.0/24` (kube-apiserver) and `10.42.0.0/24` (flannel VTEP) |
| **OPA Gatekeeper** | 9 deny-mode policies: no-latest-tag, no-privileged, allowed-registries, require-resource-limits, require-non-root, no-privilege-escalation, require-ingress-tls, no-loadbalancer-in-dev, no-hostpath |
| **Pod Security Admission** | `warn:restricted` on all namespaces; `enforce:restricted` on homer, podinfo, insurance/collab envs |
| **ESO + Vault KV** | 14 ExternalSecrets — no secrets committed to git; all credentials in HashiCorp Vault |
| **Signed commits** | GPG key `FD6D39D681DEFA34` required on `main`; CI bump commits are GPG-signed |
| **Cosign** | All 7 custom images keyless-signed via GitHub OIDC → Sigstore Fulcio |

---

## Key Rules

**Helm values location:** all values live in `helm-values/`. Do NOT edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools — those files have no effect.

**Never apply Application CRs manually.** `bootstrap/root-app.yaml` is the only file that needs a one-time `kubectl apply`. All other apps are created by the root app from `apps/`. Running `kubectl apply` on Application CRs manually competes with `selfHeal: true` and causes "missing last-applied-configuration" annotation conflicts.

**Webhook namespaces** (cert-manager, external-secrets, gatekeeper-system, keda, vault): the `allow-webhook-from-apiserver` NetworkPolicy must allow both `10.0.0.0/24` (kube-apiserver node IP) and `10.42.0.0/24` (flannel VTEP — the source IP for traffic arriving from worker-node pods).

**ResourceQuota sizing:** set quotas at ~2× steady-state to allow rolling updates. Both old and new pods count against the quota simultaneously during a rollout.

---

## Adding a New Service (Kustomize Combo 1)

```
services/<name>/
├── base/                   # no namespace, no image tag
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/                # CI auto-updates newTag here
    ├── staging/            # PR to promote
    └── prod/               # ingress + cert here
```

**Checklist:**
1. Copy `services/_template/` and replace `SERVICE_NAME`
2. Add the namespace to `manifests/argocd-project/00-project.yaml` (destinations list)
3. Add ArgoCD Application YAMLs in `apps/`
4. Update the Vault Kubernetes auth role: add `<name>-dev` + `<name>-staging` to `bound_service_account_namespaces`
5. Add `overlays/prod/ingress.yaml` + `certificate.yaml` for a public URL

---

## Tech Radar

`tech-radar.json` at the repo root contains 39 entries across 4 quadrants (Platforms, AI/ML, Security & Identity, Languages & Frameworks). It is fetched live by the Backstage Tech Radar page at `https://backstage.devandre.sbs/tech-radar` — editing this file takes effect immediately without any Backstage rebuild.
