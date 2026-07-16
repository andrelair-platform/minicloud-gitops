# minicloud-gitops

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ArgoCD: app-of-apps](https://img.shields.io/badge/ArgoCD-app--of--apps-blue)](https://argocd.devandre.sbs)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20signed-green)](https://github.com/sigstore/cosign)
[![Gatekeeper: deny mode](https://img.shields.io/badge/Gatekeeper-deny%20mode%20%E2%80%94%200%20violations-brightgreen)](https://open-policy-agent.github.io/gatekeeper)

> Single source of truth for the minicloud enterprise Kubernetes platform. Every workload — AI/ML, observability, secrets, SSO, registry, security, collaboration, and platform tooling — is declared here and reconciled automatically by ArgoCD. Git is the only write path.

**Live docs:** [andrelair-platform.github.io/minicloud-platform-docs](https://andrelair-platform.github.io/minicloud-platform-docs/)  
**Portfolio:** [devandre.sbs](https://www.devandre.sbs)  
**Live ArgoCD:** [argocd.devandre.sbs](https://argocd.devandre.sbs)

---

## Screenshots

| ArgoCD — All Platform Applications | Grafana — Kubernetes Cluster Dashboards |
|---|---|
| ![ArgoCD](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-argocd.png) | ![Grafana](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-grafana.png) |

| Homer — Platform Service Dashboard | MAAS — Bare-Metal Node Provisioning |
|---|---|
| ![Homer](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-homer.png) | ![MAAS](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/maas-machines-overview.png) |

---

## Table of Contents

- [What this repo is](#what-this-repo-is)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [AI Platform](#ai-platform)
- [Security Hardening](#security-hardening)
- [Adding a New Service](#adding-a-new-service)
- [Tech Radar](#tech-radar)
- [Key Rules](#key-rules)
- [Troubleshooting](#troubleshooting)
- [Related Repos](#related-repos)
- [License](#license)

---

## What this repo is

Every resource running in the minicloud k3s cluster originates from this repo. ArgoCD watches `apps/` via the app-of-apps pattern and reconciles all child applications automatically on every push to `main`.

**Rule:** if it runs in the cluster, its manifest or Helm values file lives here. No `kubectl apply` ever runs manually for managed workloads.

---

## Features

- **App-of-apps GitOps** — single root Application in `bootstrap/`; ArgoCD creates all child apps from `apps/` automatically; `selfHeal: true` enforces git as the only write path
- **All OPA Gatekeeper policies in deny mode, zero violations** — NET_RAW, capabilities, seccomp, privilege escalation, host namespace, allowed registries, resource limits, non-root, ingress TLS
- **Zero-trust NetworkPolicy** — default-deny ingress on all platform namespaces; services may only reach declared upstreams
- **Secrets via Vault + ESO** — all credentials in HashiCorp Vault; External Secrets Operator syncs them to Kubernetes Secrets at runtime; nothing committed to git
- **Enterprise AI stack** — LiteLLM gateway routing cloud and local LLM providers (Groq, OpenAI, Anthropic, Mistral, Gemini, Ollama); RAG pipeline (bge-m3 + pgvector HNSW + BM25 + cross-encoder + Docling OCR)
- **Full supply chain** — all custom images Trivy-scanned, Cosign-signed (keyless via GitHub OIDC → Sigstore Fulcio), syft CycloneDX SBOM as OCI referrer; GPG-signed gitops bump commits
- **Kustomize Combo 1** — base+overlays (dev/staging/prod) for internal services; CI promotes via `kustomize edit set image` to dev only; staging and prod require PR

---

## Architecture

```
MacBook Air (dev)              MAAS Controller (ThinkPad X390)
git push → GitHub             MAAS + OpenTofu (bare metal)
     |                        Ansible → k3s bootstrap
     | webhook                Tailscale endpoint + NAT
     v
minicloud-gitops (this repo — ArgoCD app-of-apps)
+-- bootstrap/      root-app.yaml (one-time apply)
+-- apps/           ArgoCD Application per workload
+-- helm-values/    all Helm overrides (canonical)
+-- services/       Kustomize base+overlays (dev/staging/prod)
+-- manifests/      cluster-wide resources (CRDs, RBAC, policies)
     |
     v (ArgoCD reconciles on every push)
+--------------------------------------------------+
|  k3s cluster — 5 nodes                          |
|  set-hog (control plane, 10.0.0.2)              |
|  fast-skunk / fast-heron / star-kitten / swift-mac|
|                                                  |
|  Secrets:   Vault (AWS KMS auto-unseal) + ESO   |
|  Identity:  Authentik OIDC + TOTP               |
|  Ingress:   nginx-ingress + cert-manager         |
|  Storage:   Longhorn (distributed, swift-mac)   |
|  Security:  Gatekeeper + Falco + NetworkPolicy  |
|  Observ:    Prometheus + Grafana + Loki          |
|  AI/ML:     LiteLLM → Groq/OpenAI/Ollama        |
|             RAG: rag-ingest + pgvector + bge-m3  |
|  Platform:  Backstage IDP + Plane CE + Harbor   |
|  Collab:    Nextcloud + OnlyOffice + Vaultwarden |
+--------------------------------------------------+
     |
  Tailscale mesh (internal — 100.x.x.x)
  Cloudflare Tunnel (public *.devandre.sbs)
```

| Component | Detail |
|---|---|
| Kubernetes | k3s — 1 control plane (set-hog) + 4 workers |
| GitOps | ArgoCD — app-of-apps, `selfHeal: true`, webhook on push |
| Secrets | HashiCorp Vault (AWS KMS auto-unseal) + External Secrets Operator |
| Storage | Longhorn distributed block storage; swift-mac as primary storage node |
| Registry | Harbor (`harbor.10.0.0.200.nip.io` internal, `harbor.devandre.sbs` public) |
| Network | Tailscale VPN mesh (internal) + Cloudflare Tunnel (public `*.devandre.sbs`) |

---

## Getting Started

```bash
# One-time bootstrap — apply the root app; ArgoCD creates all child apps automatically
kubectl apply -f bootstrap/root-app.yaml
```

All subsequent changes go through git. ArgoCD syncs on every push via webhook.

To verify cluster state locally:

```bash
kubectl --context minicloud get applications -n argocd
kubectl --context minicloud get pods -A
```

---

## AI Platform

The AI stack lives in the `ai` namespace and is fully managed here.

| Component | Description |
|---|---|
| **LiteLLM** | AI Gateway: Groq, OpenAI, Gemini, DeepSeek, Mistral, Anthropic, HuggingFace, Ollama (local) — weighted routing, circuit-breaker, Valkey cache, per-department virtual keys |
| **Ollama** × 3 | Primary + secondary (fast-heron) + tertiary (fast-skunk) — local GPU-free inference |
| **Open WebUI** | Chat interface with RAG, SearXNG web search, BM25 French + HNSW hybrid retrieval |
| **Langfuse** | LLM observability — traces, scores, cost per department key, prompt versioning |
| **Presidio** | PII/DLP guardrail — masks PERSON, PHONE, EMAIL, IP_ADDRESS before logging (DATE_TIME/LOCATION pass through to preserve financial context) |
| **markitdown-proxy** | Document converter: PDF/images → Docling OCR, Office → MarkItDown |
| **rag-ingest** | Ingest pipeline: convert → French-aware chunking → bge-m3 embed → pgvector HNSW insert |
| **postgresql-ai** | pgvector (1024-dim HNSW + GIN French FTS) for RAG; LiteLLM + Langfuse databases |
| **phi3-financial** | PromptOps pipeline — Groq llama-3.1-8b-instant primary + Ollama phi4-mini fallback; LangfusePromptHandler injects production-labelled system prompt at request time |

### LiteLLM config

LiteLLM config is managed in [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom). CI syncs `config/litellm-config.yaml` into `manifests/ai/00-litellm-configmap.yaml` automatically. **Do not edit that file directly here.**

### RAG eval pipeline

`manifests/ai/16-rag-eval-job.yaml` — ArgoCD PostSync hook that runs Ragas (GPT-4o judge) + ROUGE-L / Hit Rate / MRR after every `ai` namespace sync.  
`manifests/ai/17-rag-eval-cronjob.yaml` — 5% online sampling every 15 min with scores written back to Langfuse.

---

## Security Hardening

| Control | Detail |
|---|---|
| **NetworkPolicy** | Default-deny ingress on all platform namespaces; webhook namespaces allow both `10.0.0.0/24` (kube-apiserver) and `10.42.0.0/24` (flannel VTEP) |
| **OPA Gatekeeper** | All policies in deny mode, zero violations: no-latest-tag, no-privileged, allowed-registries, require-resource-limits, require-non-root, no-privilege-escalation, require-ingress-tls, no-loadbalancer-in-dev, no-hostpath |
| **Pod Security Admission** | `warn:restricted` on all namespaces; `enforce:restricted` on homer, podinfo, insurance/collab envs |
| **ESO + Vault KV** | All ExternalSecrets synced — no secrets committed to git; all credentials in HashiCorp Vault (AWS KMS auto-unseal) |
| **Signed commits** | GPG key `FD6D39D681DEFA34` required on `main`; CI bump commits are GPG-signed |
| **Cosign + SBOM** | All custom images keyless-signed via GitHub OIDC → Sigstore Fulcio; syft CycloneDX SBOM attached as OCI referrer |
| **Falco** | Runtime security — kernel-level syscall monitoring; alerts on unexpected process execution and file access |
| **kube-bench** | CIS k3s-1.7 benchmark — all checks pass on every worker node |

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

`tech-radar.json` at the repo root contains entries across 4 quadrants (Platforms, AI/ML, Security & Identity, Languages & Frameworks). It is fetched live by the Backstage Tech Radar page at [backstage.devandre.sbs/tech-radar](https://backstage.devandre.sbs/tech-radar) — editing this file takes effect immediately without any Backstage rebuild.

---

## Key Rules

**Helm values location:** all values live in `helm-values/`. Do NOT edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools — those files have no effect.

**Never apply Application CRs manually.** `bootstrap/root-app.yaml` is the only file that needs a one-time `kubectl apply`. All other apps are created by the root app from `apps/`. Running `kubectl apply` on Application CRs manually competes with `selfHeal: true` and causes "missing last-applied-configuration" annotation conflicts.

**Webhook namespaces** (cert-manager, external-secrets, gatekeeper-system, keda, vault): the `allow-webhook-from-apiserver` NetworkPolicy must allow both `10.0.0.0/24` (kube-apiserver node IP) and `10.42.0.0/24` (flannel VTEP — the source IP for traffic arriving from worker-node pods).

**ResourceQuota sizing:** set quotas at ~2× steady-state to allow rolling updates. Both old and new pods count against the quota simultaneously during a rollout. For single-replica workloads with a tight quota, use `strategy.type: Recreate`.

**Harbor ArgoCD loop:** do NOT set `ServerSideApply: true` on the Harbor Application. Harbor's Helm templates use `genSelfSignedCert` and `randAlphaNum` — these generate a new value on every render. With server-side apply, `ignoreDifferences` fields are not stripped, causing a sync loop and RWO PVC Multi-Attach conflicts.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| ArgoCD app stuck syncing forever after Velero upgrade | `upgradeCRDs` Helm hook Job exits 0 but k3s never sets `status.succeeded` | Set `upgradeCRDs: false` in `velero-values.yaml` and `skipCrds: true` in `apps/velero.yaml` (re-enable on next chart version bump) |
| Harbor ArgoCD sync loop triggering rolling restarts | `ServerSideApply: true` + `genSelfSignedCert`/`randAlphaNum` generates new checksums each render | Remove `ServerSideApply: true` from `apps/harbor.yaml` syncOptions |
| Rollout stalled after adding pod label to pre-Gatekeeper workload | New RS pods blocked by `K8sBlockNetRaw` — old pod predates the constraint | Add `securityContext.capabilities.drop: [NET_RAW]` in the same commit as the label change |
| New pod blocked by `K8sBlockCapabilities` on rollout | Container spec missing `capabilities.drop` list format | Gatekeeper requires the list form (`capabilities.drop: [NET_RAW]`), not the map form |
| Webhook-dependent pod fails to start with `connection refused` | NetworkPolicy missing flannel VTEP source (`10.42.0.0/24`) | Add `10.42.0.0/24` to the `allow-webhook-from-apiserver` NetworkPolicy alongside `10.0.0.0/24` |
| ESO ExternalSecret stuck in `SecretSyncedError` | Vault KV path changed or policy missing `read` permission | Check `vault kv get secret/platform/<name>` and the Vault Kubernetes auth role `bound_service_account_namespaces` |
| VPA update loop after switching to `updateMode: Auto` | Short `startupProbe` fails when VPA raises resource limits mid-start | Set `startupProbe.failureThreshold: 30` (5 min) and `minAllowed.cpu` in the VPA object |

---

## Related Repos

| Repo | Purpose |
|---|---|
| [minicloud-ansible](https://github.com/andrelair-platform/minicloud-ansible) | k3s bootstrap, Ansible roles, CIS kubelet hardening — NOT helm values |
| [minicloud-backstage](https://github.com/andrelair-platform/minicloud-backstage) | Custom Backstage image — plugins, templates, TechDocs |
| [minicloud-platform-docs](https://github.com/andrelair-platform/minicloud-platform-docs) | Docusaurus docs site → GitHub Pages |
| [minicloud-plane](https://github.com/andrelair-platform/minicloud-plane) | Go Level 4 integration: Plane API client + webhook→NATS bridge + REST API |
| [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) | Custom LiteLLM image + config sync CI |
| [minicloud-open-webui](https://github.com/andrelair-platform/minicloud-open-webui) | Custom Open WebUI image (CA cert + French BM25 baked in) |
| [minicloud-onlyoffice](https://github.com/andrelair-platform/minicloud-onlyoffice) | Custom OnlyOffice image (CA cert + NODE_EXTRA_CA_CERTS) |
| [minicloud-opentofu](https://github.com/andrelair-platform/minicloud-opentofu) | MAAS IaC (OpenTofu) — run only on controller |
| [platform-demo](https://github.com/andrelair-platform/platform-demo) | Go CI/CD demo service |
| [phi3-financial](https://github.com/andrelair-platform/phi3-financial) | PromptOps pipeline: LiteLLM CustomLogger + Langfuse + 25-case CI eval |
| [ktayl-solution-web](https://github.com/andrelair-platform/ktayl-solution-web) | Astro + Tailwind public website |

---

## License

[MIT](LICENSE) © andrelair-platform
