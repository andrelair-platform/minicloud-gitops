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

### Repository map

| Path | Role |
|---|---|
| `bootstrap/` | The app-of-apps **seed** (`root-app.yaml`) — the only thing applied by hand to bootstrap ArgoCD. |
| `apps/` | ArgoCD **`Application` manifests** = what ArgoCD watches (the taxonomy projection — see `ARCHITECTURE.md`): `platform/<layer>/` · `is/<group>/` · `retrieva/` · `previews/`. (`workloads/` is **retired** — the Architecture-Guard CI blocks new entries there.) |
| `platform/<layer>/` | **Platform capabilities** (domain-agnostic) by layer — `foundation` · `networking` · `secrets` · `security` · `observability` · `data` · `ai` · `delivery` · `storage` · `automation` · `shared-services`. Holds the raw K8s/CRD manifests (network-policies, quotas, gatekeeper-policies, argocd-project…). |
| `is/<group>/` | **Information-System** (the insurance business) resources — `insurance` · `erp` · `workplace`. |
| `services/<svc>/` | Per-custom-app **packaging**: `helm/` (GAP **wrapper chart** — the standard) + `kargo/` (promotion pipeline). **Helm-only — zero kustomize.** |
| `charts/` | The shared **`minicloud-app-deployment` library chart** (the golden path consumed by every wrapper chart). |
| `helm-values/` | Values for **third-party** Helm charts (Grafana/Vault/Harbor/ERPNext…) consumed by `apps/platform`. |
| `environments/overlays/{dev,prod}` | Shared per-environment config. |
| `bmad/` | Story authoring — `templates/` + this product's stories (`stories/platform/`). Per-product BMAD otherwise lives in each product's home repo. |
| `docs/` | **In-repo ADRs** — design decisions coupled to the code (`helm-golden-path.md`), reviewed in the same PR. Reference/governance docs live on the org site ([minicloud-platform-docs](https://andrelair-platform.github.io/minicloud-platform-docs/), e.g. the *AI Model Governance Matrix* / *DORA Audit Trail* under AI & ML). Rule: **ADRs/runbooks with the code; reference & governance on the org site.** No per-repo Docusaurus site for this infra repo. |
| `scripts/github-project/` | GitHub Projects sprint-assignment helpers. |
| root | `catalog-info.yaml` (Backstage), `README`, `CHANGELOG`, release-please, renovate, `tech-radar.json`. |

---

## Features

- **App-of-apps GitOps** — single root Application in `bootstrap/`; ArgoCD creates all child apps from `apps/` automatically; `selfHeal: true` enforces git as the only write path
- **All OPA Gatekeeper policies in deny mode, zero violations** — NET_RAW, capabilities, seccomp, privilege escalation, host namespace, allowed registries, resource limits, non-root, ingress TLS
- **Zero-trust NetworkPolicy** — default-deny ingress on all platform namespaces; services may only reach declared upstreams
- **Secrets via Vault + ESO** — all credentials in HashiCorp Vault; External Secrets Operator syncs them to Kubernetes Secrets at runtime; nothing committed to git
- **Enterprise AI stack** — LiteLLM gateway routing cloud and local LLM providers (Groq, OpenAI, Anthropic, Mistral, Gemini, Ollama); RAG pipeline (bge-m3 + **Qdrant** vector DB + BM25 + cross-encoder + Docling OCR)
- **Full supply chain** — all custom images Trivy-scanned, Cosign-signed (keyless via GitHub OIDC → Sigstore Fulcio), syft CycloneDX SBOM as OCI referrer; GPG-signed gitops bump commits
- **Helm GAP wrapper-chart + Kargo promotion** — each custom app is a thin Helm chart on the shared `minicloud-app-deployment` library (no kustomize); **two environments only** (`dev` + `prod`); **Kargo** promotes one immutable image `dev → prod` (dev auto-merge · prod CODEOWNERS-gated PR)

---

## Architecture

**The GitOps workflow system** — humans and Kargo only ever write to **Git (the single source of truth)**;
**ArgoCD is the only thing that writes to the cluster**, continuously reconciling desired state (Git)
against live state and self-healing drift (the red loop). This is the control loop this repo implements:

<p align="center">
  <img src="https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/architecture/platform-gitops-system.png"
       alt="GitOps workflow system — Git is the source of truth, ArgoCD is the only cluster writer" width="560" />
</p>

> Full system-design set (System Context · Container · Delivery Pipeline · GitOps System) on the
> [Architecture docs → C4 System Design](https://andrelair-platform.github.io/minicloud-platform-docs/platform/architecture/c4-system-design).

```
MacBook Air (dev)              MAAS Controller (ThinkPad X390)
git push → GitHub             MAAS + OpenTofu (bare metal)
     |                        Ansible → k3s bootstrap
     | webhook                Tailscale endpoint + NAT
     v
minicloud-gitops (this repo — ArgoCD app-of-apps)
+-- bootstrap/      root-app.yaml (one-time apply)
+-- apps/           ArgoCD Application per workload (platform · is · retrieva · previews)
+-- platform/       platform capabilities by layer (ai, security, observability…)
+-- is/             insurance-business resources (insurance · erp · workplace)
+-- services/       custom-app packaging — helm/ wrapper chart + kargo/ (Helm-only)
+-- helm-values/    third-party chart values (helm-values/minicloud-1/)
     |
     v (ArgoCD reconciles on every push; Kargo promotes dev → prod)
+--------------------------------------------------+
|  k3s cluster — 6 nodes (1 control plane + 5 workers) |
|  set-hog (control plane, 10.0.0.2)                   |
|  fast-skunk · fast-heron · star-kitten ·            |
|  loving-gannet · swift-mac                           |
|  CNI: Cilium (CNI + LB-IPAM 10.0.0.200 + Hubble)    |
|                                                  |
|  Secrets:   Vault (AWS KMS auto-unseal) + ESO   |
|  Identity:  Authentik OIDC + TOTP               |
|  Ingress:   nginx-ingress + cert-manager         |
|  Storage:   Longhorn (replicated: heron/gannet/swift)|
|  Security:  Gatekeeper + Falco + NetworkPolicy  |
|  Observ:    Prometheus + Grafana + Loki + Tempo + OTel|
|  AI/ML:     LiteLLM → Groq/OpenAI/Ollama        |
|             RAG: rag-ingest + Qdrant + bge-m3   |
|  Platform:  Backstage IDP + Plane CE + Harbor   |
|  Collab:    Nextcloud + OnlyOffice + Vaultwarden |
+--------------------------------------------------+
     |
  Tailscale mesh (internal — 100.x.x.x)
  Cloudflare Tunnel (public *.devandre.sbs)
```

| Component | Detail |
|---|---|
| Kubernetes | k3s — 1 control plane (set-hog) + 5 workers (fast-skunk, fast-heron, star-kitten, loving-gannet, swift-mac) |
| GitOps | ArgoCD — app-of-apps, `selfHeal: true`, webhook on push; **Kargo** promotes `dev → prod` |
| CNI / LB | **Cilium** — CNI + LB-IPAM (`10.0.0.200`) + Hubble (replaced flannel + MetalLB) |
| Secrets | HashiCorp Vault (AWS KMS auto-unseal) + External Secrets Operator |
| Storage | Longhorn distributed block storage (replicated across fast-heron / loving-gannet / swift-mac) |
| Registry | **Hybrid** — Harbor (`harbor.10.0.0.200.nip.io`) for dev images · **ghcr.io** for prod (immutable SHA, cosign-signed) |
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
| **Qdrant** | Vector DB — the RAG retrieval store (HNSW); `platform/ai/litellm/42-qdrant.yaml` |
| **rag-ingest** | Ingest pipeline: convert → French-aware chunking → bge-m3 embed → **Qdrant** insert |
| **postgresql-ai** | Postgres for the **LiteLLM** metadata DB (Langfuse moved to its own CNPG cluster `langfuse-postgres`) |

### LiteLLM config

LiteLLM config is managed in [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom). CI syncs `config/litellm-config.yaml` into `platform/ai/litellm/00-litellm-configmap.yaml` automatically. **Do not edit that file directly here.**

### RAG eval pipeline

`platform/ai/litellm/16-rag-eval-job.yaml` — ArgoCD PostSync hook that runs Ragas (GPT-4o judge) + ROUGE-L / Hit Rate / MRR after every `ai` namespace sync.  
`platform/ai/litellm/17-rag-eval-cronjob.yaml` — 5% online sampling every 15 min with scores written back to Langfuse.

---

## Security Hardening

| Control | Detail |
|---|---|
| **NetworkPolicy** | Default-deny ingress on all platform namespaces; apiserver/webhook reachability uses a **CiliumNetworkPolicy `toEntities`** (`kube-apiserver` · `host` · `remote-node`) — the Cilium identity, not a flannel CIDR |
| **OPA Gatekeeper** | All policies in deny mode, zero violations: no-latest-tag, no-privileged, allowed-registries, require-resource-limits, require-non-root, no-privilege-escalation, require-ingress-tls, no-loadbalancer-in-dev, no-hostpath |
| **Pod Security Admission** | `warn:restricted` on all namespaces; `enforce:restricted` on homer, podinfo, insurance/collab envs |
| **ESO + Vault KV** | All ExternalSecrets synced — no secrets committed to git; all credentials in HashiCorp Vault (AWS KMS auto-unseal) |
| **Signed commits** | GPG key `FD6D39D681DEFA34` required on `main`; CI bump commits are GPG-signed |
| **Cosign + SBOM** | All custom images keyless-signed via GitHub OIDC → Sigstore Fulcio; syft CycloneDX SBOM attached as OCI referrer |
| **Falco** | Runtime security — kernel-level syscall monitoring; alerts on unexpected process execution and file access |
| **kube-bench** | CIS k3s-1.7 benchmark — all checks pass on every worker node |

---

## Adding a New Service (GAP wrapper-chart golden path)

A custom app is **its own thin Helm chart** that depends on the shared `minicloud-app-deployment`
library chart — no kustomize, one ArgoCD Helm source. Full workflow:
[delivery-workflow](https://andrelair-platform.github.io/minicloud-platform-docs/developer-platform/delivery-workflow)
· scaffold: `services/_template-helm/` · design: [`docs/helm-golden-path.md`](docs/helm-golden-path.md).

```
services/<name>/helm/
├── Chart.yaml        # dependencies: minicloud-app-deployment @ X.Y.Z (oci://ghcr.io/andrelair-platform)
├── Chart.lock        # committed — ArgoCD runs `helm dependency build`
├── values.yaml       # common: "minicloud-app-deployment:" block + wrapper-local keys
├── values-dev.yaml   # dev overlay  (image.tag, hosts)  ← Kargo yaml-updates this
├── values-prod.yaml  # prod overlay (image.tag, hosts, replicas)
└── templates/        # service-specific extras the library can't cover (DB, AnalysisTemplate, ES…)
```

**Checklist:**

1. Copy `services/_template-helm/` → `services/<name>/helm/`; replace `SERVICE_NAME`; `helm dependency update .` → commit `Chart.lock`.
2. Fill `values.yaml` (under the `minicloud-app-deployment:` key) + `values-{dev,prod}.yaml`.
3. Create the two Argo CD Application files under the service's **taxonomy home** — `apps/is/<group>/<name>-{dev,prod}.yaml` for a business/IS app or `apps/platform/<layer>/<name>-{dev,prod}.yaml` for a platform capability (NOT `apps/workloads/` — retired; the Architecture Guard CI blocks new entries there); keep `helm.releaseName: <name>`.
4. Add the namespaces to `manifests/argocd-project/00-project.yaml`; update the Vault k8s auth role.
5. Add a Kargo pipeline (`services/<name>/kargo/`) — promotion does a `yaml-update` on `minicloud-app-deployment.image.tag`.

> Validate locally: `cd services/<name>/helm && helm dependency update . && helm template <name> . -f values-dev.yaml`
> Gotchas (Chart.lock, `.helmignore`, `releaseName`, `{{ }}` escaping, `selectorLabels`): see `.claude/rules/gitops.md`.

---

## Tech Radar

`tech-radar.json` at the repo root contains entries across 4 quadrants (Platforms, AI/ML, Security & Identity, Languages & Frameworks). It is fetched live by the Backstage Tech Radar page at [backstage.devandre.sbs/tech-radar](https://backstage.devandre.sbs/tech-radar) — editing this file takes effect immediately without any Backstage rebuild.

---

## Key Rules

**Helm values location:** all values live in `helm-values/`. Do NOT edit `minicloud-ansible/helm-values/` for ArgoCD-managed tools — those files have no effect.

**Never apply Application CRs manually.** `bootstrap/root-app.yaml` is the only file that needs a one-time `kubectl apply`. All other apps are created by the root app from `apps/`. Running `kubectl apply` on Application CRs manually competes with `selfHeal: true` and causes "missing last-applied-configuration" annotation conflicts.

**Webhook namespaces** (cert-manager, external-secrets, gatekeeper-system, keda, vault): under **Cilium**, a plain `ipBlock` CIDR does **not** match the kube-apiserver identity — use a **CiliumNetworkPolicy** `toEntities: [kube-apiserver, host, remote-node]` so admission webhooks stay reachable. (The old flannel `10.42.0.0/24` CIDR rule no longer applies.)

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
| Webhook-dependent pod fails to start with `connection refused` | Under Cilium, an `ipBlock` CIDR doesn't match the kube-apiserver identity | Use a **CiliumNetworkPolicy** `toEntities: [kube-apiserver, host, remote-node]` (not a flannel `10.42.0.0/24` ipBlock) |
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
| [ktayl-solution-web](https://github.com/andrelair-platform/ktayl-solution-web) | Astro + Tailwind public website |

---

## License

[MIT](LICENSE) © andrelair-platform
