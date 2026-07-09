# minicloud-gitops — GitOps source-of-truth

ArgoCD app-of-apps source for the minicloud enterprise Kubernetes platform.
Every commit to `main` triggers a cluster reconciliation within ~3 minutes.

**Live docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>  
**Portfolio:** <https://www.devandre.sbs>

**Sibling repos:** [docs](https://github.com/andrelair-platform/minicloud-platform-docs) · [ansible](https://github.com/andrelair-platform/minicloud-ansible) · [platform-demo](https://github.com/andrelair-platform/platform-demo) · [rag-ingest](https://github.com/andrelair-platform/minicloud-rag-ingest)

---

## Platform Overview

Production-grade enterprise Kubernetes platform on 4 bare-metal ThinkPad laptops (k3s). 54+ workloads managed via ArgoCD GitOps. 62 automated regression checks continuously green.

| Layer | Components |
|---|---|
| **GitOps** | ArgoCD app-of-apps, Kustomize base+overlays (dev/staging/prod), 3-branch CI promotion |
| **Security** | 9/9 OPA Gatekeeper admission policies (deny mode, 0 violations), zero-trust NetworkPolicy across 23 namespaces, Vault auto-unseal (AWS KMS), cosign + SBOM supply chain |
| **AI** | Enterprise AI Gateway (LiteLLM, 8 providers), RAG pipeline (bge-m3 + pgvector HNSW + BM25 French + cross-encoder), Langfuse LLMOps |
| **Observability** | Prometheus/Grafana/Loki/Alertmanager, Falco runtime security, Polaris workload quality |
| **Identity** | Authentik OIDC SSO, 16 department groups, RBAC personas verified |

---

## Enterprise AI Gateway

Multi-provider LLM routing and enterprise governance platform built on LiteLLM.
Unified 8 cloud and local providers behind a single API endpoint.

### Architecture

```
                        ┌─────────────────────────────────────┐
                        │        litellm.devandre.sbs         │
                        │   (Cloudflare Tunnel → NGINX → k3s) │
                        └──────────────┬──────────────────────┘
                                       │ /v1/chat/completions
                        ┌──────────────▼──────────────────────┐
                        │         LiteLLM Router               │
                        │  ┌─────────────────────────────┐    │
                        │  │   Presidio pre_call_hook    │    │  ← PII/DLP masking
                        │  │   (DATE_TIME + LOCATION     │    │    before any provider
                        │  │    excluded for finance)    │    │    sees the prompt
                        │  └─────────────────────────────┘    │
                        │  ┌─────────────────────────────┐    │
                        │  │   Valkey exact-match cache  │    │  ← 600s TTL
                        │  └─────────────────────────────┘    │
                        │  ┌─────────────────────────────┐    │
                        │  │   Circuit breaker           │    │  ← cooldown=60s
                        │  │   (allowed_fails=3)         │    │    failed→quarantine
                        │  └─────────────────────────────┘    │
                        └──┬───────┬───────┬──────────┬───────┘
                           │       │       │          │
              ┌────────────▼─┐ ┌───▼────┐ ┌▼──────┐ ┌▼────────────┐
              │ Ollama local │ │  Groq  │ │OpenAI │ │  DeepSeek   │
              │ phi4-mini    │ │llama-  │ │gpt-4o │ │  reasoner   │
              │ qwen3.5:4b   │ │3.1-8b  │ │gpt-4o-│ │  (cloud-    │
              │ deepseek-r1  │ │instant │ │mini   │ │   first)    │
              └──────────────┘ └────────┘ └───────┘ └─────────────┘
              + Mistral + Gemini + Anthropic Claude + HuggingFace + NVIDIA NIM
```

**Fallback chain:** `Ollama → Groq → DeepSeek` — automatic, zero application changes  
**Budget enforcement:** at the LiteLLM VirtualKey layer, not the application  
**Secrets:** all 8 provider API keys from HashiCorp Vault via ESO ExternalSecret — zero secrets in git

### Department Key Governance (3 tiers)

| Tier | Departments | Budget | Models |
|---|---|---|---|
| Premium | IT, Data, Actuariat, Transformation | $100/30d | All models |
| Standard | Cyber, Finance, Audit, Juridique, Réassurance, Commercial, Souscription | $30/30d | Standard cloud + local |
| Basic | Sinistres, Ops, RH, SG | $5/30d | Local models only |

### Live Endpoints

**API — callable right now:**

```bash
# List available models (public, no auth required)
curl https://litellm.devandre.sbs/v1/models

# Chat completions via the enterprise gateway (demo key: $0.50 cap, groq-fallback only)
curl -s -X POST https://litellm.devandre.sbs/v1/chat/completions \
  -H "Authorization: Bearer sk-portfolio-demo" \
  -H "Content-Type: application/json" \
  -d '{"model": "groq-fallback", "messages": [{"role": "user", "content": "What is an LLM gateway?"}], "max_tokens": 60}'
```

> The demo key (`sk-portfolio-demo`) is rate-limited to `groq-fallback` + `phi4-mini`, capped at $0.50/30 days.  
> Every call above is traced in Langfuse and increments the Grafana spend counter — live evidence that the full observability stack is wired.

**Dashboards:**

| Service | URL |
|---|---|
| AI Gateway (model list) | <https://litellm.devandre.sbs/v1/models> |
| Grafana cost dashboard | <https://grafana.devandre.sbs/d/litellm-cost-dept> |
| Langfuse LLMOps tracing | <https://langfuse.devandre.sbs> |
| Open WebUI (chat interface) | <https://chat.devandre.sbs> |

### Screenshots

**Grafana — LiteLLM Spend & Usage (live SQL against LiteLLM_SpendLogs)**

![Grafana cost dashboard showing $1.67 spend, 2.52M tokens, 1.38K requests](docs/ai-gateway/screenshots/grafana-litellm-cost.png)

*PostgreSQL datasource provisioned via ESO + Grafana sidecar ConfigMap. Dashboard JSON stored in git as a ConfigMap labelled `grafana_dashboard: "1"` — injected without any UI interaction.*

---

**Langfuse — phi3-financial Eval Trace (correctness: 1.00)**

![Langfuse trace eval-T11 showing phi3-financial response with correctness score 1.00](docs/ai-gateway/screenshots/langfuse-phi3-trace.png)

*Trace eval-T11 from the RAG eval CI gate. Input: "Explain the difference between a call option and a put option." Tagged `prompt-eval`, git release pinned. Ragas faithfulness=0.80, hit_rate=0.80.*

---

**Langfuse — 25-Trace Eval Pipeline**

![Langfuse tracing list showing all 25 eval traces T1-T25 with metric columns](docs/ai-gateway/screenshots/langfuse-eval-traces.png)

*All 25 eval traces (T1–T25) from the ArgoCD PostSync CI gate. Financial domain questions with per-trace correctness scores. Columns: answer_relevancy, faithfulness, hit_rate, mrr, rouge_l.*

---

### Key Implementation Files

| File | Purpose |
|---|---|
| `helm-values/litellm-values.yaml` | LiteLLM Helm — 8 providers, circuit breaker, Presidio hook |
| `manifests/ai/00-litellm-configmap.yaml` | Router models, fallback chain, Presidio guardrail config |
| `manifests/ai/06-langfuse.yaml` | Langfuse v3.201.1 + ClickHouse + Valkey |
| `manifests/ai/07-litellm-grafana-dashboard.yaml` | Cost dashboard ConfigMap (sidecar-injected) |
| `manifests/eso-platform-secrets/10-ai-postgresql.yaml` | Vault → 8 provider API keys |
| `manifests/eso-platform-secrets/12-grafana-litellm-db.yaml` | Vault → Grafana PostgreSQL password |
| `docs/ai-gateway/dept-key-governance.md` | Department key structure and allowlist details |

---

## Repository Layout

```
.
├── bootstrap/
│   └── root-app.yaml              # single ArgoCD Application that watches apps/
├── apps/                          # one Application YAML per workload (54+ apps)
│   ├── litellm.yaml               # Enterprise AI Gateway (multi-source Helm)
│   ├── langfuse.yaml              # Langfuse LLMOps
│   ├── ollama.yaml                # Ollama primary (fast-heron, local-path NVMe)
│   ├── open-webui.yaml            # Open WebUI chat interface
│   └── ...
├── helm-values/                   # all Helm values (post-migration 2026-07-07)
│   ├── litellm-values.yaml
│   ├── kube-prometheus-stack-values.yaml
│   └── ...
├── manifests/                     # raw Kubernetes manifests
│   ├── ai/                        # LiteLLM config, Langfuse, RAG, Grafana dashboard
│   ├── argocd-project/            # AppProject with locked sourceRepos + whitelist
│   ├── eso-platform-secrets/      # ExternalSecrets (13 secrets from Vault)
│   ├── network-policies/          # default-deny + allow rules across 23 namespaces
│   ├── quotas/                    # ResourceQuota + LimitRange per namespace
│   └── gatekeeper-policies/       # 9 OPA ConstraintTemplates + Constraints
├── services/                      # Kustomize base+overlays for internal services
│   ├── platform-demo/             # Go CI/CD demo (base + dev/staging/prod overlays)
│   └── _template/                 # scaffold for new services
└── docs/
    └── ai-gateway/
        ├── dept-key-governance.md
        └── screenshots/           # evidence from running production system
```

## Bootstrap

```bash
# One-time: apply the root app — ArgoCD creates all child apps from apps/
kubectl apply -f bootstrap/root-app.yaml
```

## Regression Checks

62-check automated regression suite runs after every significant change:

```bash
ssh controller "bash ~/minicloud-ktaylorganisation/scripts/regression-check.sh"
```

Latest result: **62 PASS / 0 FAIL / 0 WARN** (regression check #26)

Covers: ArgoCD sync state, cert readiness, PVC bindings, ESO sync, Gatekeeper violations, Vault unseal, Ollama models, RBAC personas, disk usage, Langfuse tracing, Grafana datasource, LiteLLM routing.
