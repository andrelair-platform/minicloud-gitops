# minicloud-gitops

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ArgoCD: app-of-apps](https://img.shields.io/badge/ArgoCD-app--of--apps-blue)](https://argocd.devandre.sbs)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20signed-green)](https://github.com/sigstore/cosign)
[![Gatekeeper: deny mode](https://img.shields.io/badge/Gatekeeper-deny%20mode%20%E2%80%94%200%20violations-brightgreen)](https://open-policy-agent.github.io/gatekeeper)

> **Single source of truth for the minicloud enterprise Kubernetes platform.** Every workload — AI, observability, secrets, SSO, registry, security, the digital workplace, and the insurance business apps — is declared here and reconciled by ArgoCD. **Git is the only write path.**

**Docs:** [minicloud-platform-docs](https://andrelair-platform.github.io/minicloud-platform-docs/) ·
**Architecture (C4):** [system design](https://andrelair-platform.github.io/minicloud-platform-docs/platform/architecture/c4-system-design) ·
**Live ArgoCD:** [argocd.devandre.sbs](https://argocd.devandre.sbs) ·
**Portfolio:** [devandre.sbs](https://www.devandre.sbs)

| ArgoCD — Applications | Grafana — Cluster | Homer — Services | MAAS — Bare metal |
|---|---|---|---|
| ![ArgoCD](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-argocd.png) | ![Grafana](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-grafana.png) | ![Homer](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/screenshot-homer.png) | ![MAAS](https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/maas-machines-overview.png) |

---

## The model — two pillars, one write path

The repo is organised around a single boundary (the law is [`ARCHITECTURE.md`](ARCHITECTURE.md)):

- **`platform/`** — technical **capabilities** the platform *provides* (domain-agnostic: compute, networking, secrets, SSO, observability, AI, data, delivery).
- **`is/`** — the **Information System** that *consumes* them: the insurance business apps, data and the digital workplace.
- **`services/`** = *how* custom apps are packaged (Helm wrapper chart + Kargo). **`apps/`** = *where* ArgoCD classifies and deploys them.

> **Litmus test:** *if the company stopped selling insurance tomorrow, would this still exist?* **Yes → `platform/` · No → `is/`.**

**How a change reaches the cluster** — humans and Kargo only ever write to **Git (the single source of truth)**; **ArgoCD is the only thing that writes to the cluster**, continuously reconciling desired state (Git) against live state and self-healing drift (the red loop):

<p align="center">
  <img src="https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/architecture/platform-gitops-system.png"
       alt="GitOps workflow system — Git is the source of truth, ArgoCD is the only cluster writer" width="560" />
</p>

> Full system-design set (System Context · Container · Delivery Pipeline · GitOps System) → [Architecture docs → C4 System Design](https://andrelair-platform.github.io/minicloud-platform-docs/platform/architecture/c4-system-design).

---

## Repository map

| Path | Role |
|---|---|
| `bootstrap/` | The app-of-apps **seed** (`root-app.yaml`) — the only thing applied by hand. |
| `apps/` | ArgoCD **`Application`** manifests (the taxonomy projection): `platform/<layer>/` · `is/<group>/` · `retrieva/` · `previews/`. |
| `platform/<layer>/` | **Platform capabilities** by layer — `foundation` · `networking` · `secrets` · `security` · `observability` · `data` · `ai` · `delivery` · `storage` · `automation` · `shared-services`. Holds the raw K8s/CRD manifests (netpols, quotas, gatekeeper-policies…). |
| `is/<group>/` | **Information-System** resources — `insurance` · `erp` · `workplace`. |
| `services/<svc>/` | Per-custom-app packaging: `helm/` (GAP **wrapper chart**) + `kargo/` (promotion). **Helm-only — zero kustomize.** |
| `charts/` | The shared **`minicloud-app-deployment` library chart** (the golden path). |
| `helm-values/` | Values for **third-party** Helm charts (Grafana/Vault/Harbor/ERPNext…). |
| `docs/` | **In-repo ADRs** (design coupled to code). Reference & governance docs live on the [org site](https://andrelair-platform.github.io/minicloud-platform-docs/). |
| `bmad/` · `scripts/` · root | Story templates; repo-ops helpers; `catalog-info.yaml`, release-please, renovate, `tech-radar.json`. |

---

## The cluster

| Layer | Choice |
|---|---|
| **Kubernetes** | k3s — **6 nodes**: 1 control plane (`set-hog`) + 5 workers (`fast-skunk`, `fast-heron`, `star-kitten`, `loving-gannet`, `swift-mac`) |
| **CNI / LB** | **Cilium** — CNI + LB-IPAM (`10.0.0.200`) + Hubble (replaced flannel + MetalLB) |
| **GitOps** | ArgoCD (app-of-apps, `selfHeal: true`) + **Kargo** promoting one immutable image `dev → prod` (prod CODEOWNERS-gated) |
| **Secrets** | HashiCorp Vault (AWS KMS auto-unseal) + External Secrets Operator — nothing committed to git |
| **Identity** | Authentik — OIDC + TOTP (SSO for every app) |
| **Ingress / TLS** | nginx-ingress + cert-manager |
| **Storage** | Longhorn distributed block storage (replicated across `fast-heron` / `loving-gannet` / `swift-mac`) |
| **Registry** | **Hybrid** — Harbor (`harbor.10.0.0.200.nip.io`) for dev · **ghcr.io** for prod (immutable SHA, cosign-signed) |
| **Observability** | Prometheus · Grafana · Loki · Tempo · OTel |
| **Security** | Gatekeeper (deny mode, 0 violations) · Falco · default-deny NetworkPolicy |
| **AI** | LiteLLM gateway · Qdrant (RAG) · Langfuse · Ollama (local) |
| **Network** | Tailscale mesh (internal) + Cloudflare Tunnel (public `*.devandre.sbs`) |

---

## Getting started

```bash
# One-time bootstrap — apply the root app; ArgoCD creates every child app from apps/
kubectl apply -f bootstrap/root-app.yaml

# Verify
kubectl --context minicloud get applications -n argocd
kubectl --context minicloud get pods -A
```

All subsequent changes go through **git → PR → ArgoCD**. No `kubectl apply` is ever run manually for managed workloads — that competes with `selfHeal: true`.

---

## Adding a new service (GAP wrapper-chart golden path)

A custom app is **its own thin Helm chart** that depends on the shared `minicloud-app-deployment` library chart — one ArgoCD Helm source, no kustomize. Reference chart: `services/platform-demo/helm/` · design: [`docs/helm-golden-path.md`](docs/helm-golden-path.md) · full workflow: [delivery-workflow](https://andrelair-platform.github.io/minicloud-platform-docs/platform/developer-platform/delivery-workflow).

```
services/<name>/helm/
├── Chart.yaml        # dependencies: minicloud-app-deployment @ X.Y.Z (oci://ghcr.io/andrelair-platform)
├── Chart.lock        # committed — ArgoCD runs `helm dependency build`
├── values.yaml       # "minicloud-app-deployment:" block + wrapper-local keys
├── values-dev.yaml   # dev overlay  ← Kargo yaml-updates image.tag
├── values-prod.yaml  # prod overlay
└── templates/        # service-specific extras (DB, AnalysisTemplate, ExternalSecret…)
```

1. Copy a reference chart (e.g. `services/platform-demo/helm/`) → `services/<name>/helm/`; `helm dependency update .` → commit `Chart.lock`.
2. Fill `values.yaml` + `values-{dev,prod}.yaml`.
3. Create the two ArgoCD `Application`s under the taxonomy home — `apps/is/<group>/` (business app) or `apps/platform/<layer>/` (platform capability); keep `helm.releaseName: <name>`.
4. Add the namespaces to `platform/delivery/argocd-project/`; update the Vault k8s auth role.
5. Add a Kargo pipeline (`services/<name>/kargo/`) — promotion is a `yaml-update` on `minicloud-app-deployment.image.tag`.

> Validate locally: `cd services/<name>/helm && helm dependency update . && helm template <name> . -f values-dev.yaml`.
> Gotchas (Chart.lock, `.helmignore`, `releaseName`, `{{ }}` escaping): [`.claude/rules/gitops.md`](.claude/rules/gitops.md).

---

## AI platform (`platform/ai/`)

| Component | Role |
|---|---|
| **LiteLLM** | AI gateway — Groq / OpenAI / Gemini / Mistral / Anthropic / Ollama; weighted routing, circuit-breaker, Valkey cache, per-department virtual keys + budgets |
| **Qdrant** | Vector DB — the RAG retrieval store (HNSW) |
| **rag-ingest** | Ingest: convert → French-aware chunking → bge-m3 embed → **Qdrant** insert |
| **Open WebUI** | Chat UI with RAG, web search, BM25-French + HNSW hybrid retrieval |
| **Langfuse** | LLM observability — traces, scores, cost per key, prompt versioning |
| **Presidio** | PII/DLP guardrail — masks PERSON/PHONE/EMAIL/IP before logging |
| **markitdown-proxy** | PDF/images → Docling OCR · Office → MarkItDown |
| **postgresql-ai** | Postgres for the LiteLLM metadata DB (Langfuse runs on its own CNPG cluster) |

LiteLLM config is owned by [minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) and CI-synced into `platform/ai/litellm/00-litellm-configmap.yaml` — **don't edit it here**. RAG quality is gated by a Ragas eval (`platform/ai/litellm/16-rag-eval-job.yaml`, ArgoCD PostSync) + 5% online sampling to Langfuse (`17-rag-eval-cronjob.yaml`).

---

## Security hardening

| Control | Detail |
|---|---|
| **NetworkPolicy** | Default-deny ingress on all platform namespaces; apiserver/webhook reachability via **CiliumNetworkPolicy `toEntities: [kube-apiserver, host, remote-node]`** (Cilium identity, not a CIDR) |
| **OPA Gatekeeper** | All policies in **deny mode, zero violations** — no-latest-tag, no-privileged, allowed-registries, resource-limits, non-root, no-privilege-escalation, ingress-TLS, no-hostpath, no-hostname-pin |
| **Secrets** | ESO + Vault KV (AWS KMS auto-unseal) — no secrets in git |
| **Supply chain** | Trivy scan + keyless **Cosign** signing (GitHub OIDC → Sigstore Fulcio) + syft CycloneDX SBOM; GPG-signed commits (`FD6D39D681DEFA34` required on `main`) |
| **Runtime** | Falco (syscall monitoring) · Pod Security Admission (`restricted`) · kube-bench (CIS k3s-1.7) |

---

<details>
<summary><b>Operations</b> — key rules & troubleshooting</summary>

### Key rules

- **Helm values** all live in `helm-values/` — editing `minicloud-ansible/helm-values/` has no effect.
- **Never apply `Application` CRs manually** — `bootstrap/root-app.yaml` is the only one-time `kubectl apply`; the rest come from the root app. Manual apply fights `selfHeal`.
- **Webhook namespaces** (cert-manager, external-secrets, gatekeeper-system, keda, vault): under Cilium an `ipBlock` CIDR does **not** match the kube-apiserver identity — use a **CiliumNetworkPolicy** `toEntities: [kube-apiserver, host, remote-node]`.
- **ResourceQuota sizing** at ~2× steady state (old + new pods coexist during a rollout); single-replica + tight quota → `strategy.type: Recreate`.
- **Harbor** Application: do **not** set `ServerSideApply: true` — its `genSelfSignedCert`/`randAlphaNum` render new values each sync → loop + RWO Multi-Attach.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| ArgoCD app stuck syncing after Velero upgrade | `upgradeCRDs` hook Job exits 0 but k3s never sets `status.succeeded` | `upgradeCRDs: false` + `skipCrds: true` (re-enable on next chart bump) |
| Harbor sync loop / rolling restarts | `ServerSideApply: true` + `genSelfSignedCert` new checksum each render | Remove `ServerSideApply: true` from `apps/.../harbor.yaml` |
| Webhook pod `connection refused` | Under Cilium an ipBlock CIDR doesn't match the apiserver identity | CiliumNetworkPolicy `toEntities: [kube-apiserver, host, remote-node]` (not a flannel `10.42.0.0/24` ipBlock) |
| New pod blocked by `K8sBlockCapabilities` | Container missing `capabilities.drop` in list form | Use `capabilities.drop: [NET_RAW]` (list, not map) |
| ESO `SecretSyncedError` | Vault KV path changed / policy missing `read` | Check `vault kv get secret/platform/<name>` + the Vault k8s-auth role namespaces |
| VPA update loop on `updateMode: Auto` | Short `startupProbe` fails when VPA raises limits mid-start | `startupProbe.failureThreshold: 30` + `minAllowed.cpu` on the VPA |

</details>

---

## Tech Radar

`tech-radar.json` (repo root) feeds the Backstage [Tech Radar](https://backstage.devandre.sbs/tech-radar) live — edit it and it takes effect with no rebuild.

## Related repos

[minicloud-ansible](https://github.com/andrelair-platform/minicloud-ansible) (k3s bootstrap) ·
[minicloud-opentofu](https://github.com/andrelair-platform/minicloud-opentofu) (MAAS IaC) ·
[minicloud-backstage](https://github.com/andrelair-platform/minicloud-backstage) ·
[minicloud-platform-docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) ·
[minicloud-open-webui](https://github.com/andrelair-platform/minicloud-open-webui) ·
[minicloud-onlyoffice](https://github.com/andrelair-platform/minicloud-onlyoffice) ·
[minicloud-plane](https://github.com/andrelair-platform/minicloud-plane) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo) ·
[ktayl-solution-web](https://github.com/andrelair-platform/ktayl-solution-web)

## License

[MIT](LICENSE) © andrelair-platform
