# minicloud-gitops

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ArgoCD: app-of-apps](https://img.shields.io/badge/ArgoCD-app--of--apps-blue)](https://argocd.devandre.sbs)
[![Promotion: Kargo](https://img.shields.io/badge/promotion-Kargo%20dev%E2%86%92prod-0ea5e9)](https://kargo.akuity.io)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20%2B%20SBOM-green)](https://github.com/sigstore/cosign)
[![Gatekeeper: deny mode](https://img.shields.io/badge/Gatekeeper-deny%20mode%20%E2%80%94%200%20violations-brightgreen)](https://open-policy-agent.github.io/gatekeeper)

> **The declarative source of truth for the minicloud platform.** One Git repository defines every workload — the platform's technical capabilities and the insurance Information System alike — and **ArgoCD is the only process that writes to the cluster.** People and automation change the system by changing Git; the cluster is continuously reconciled to match. There are no snowflakes and no manual `kubectl apply`.

**Docs:** [platform docs](https://andrelair-platform.github.io/minicloud-platform-docs/) ·
**Architecture (C4):** [system design](https://andrelair-platform.github.io/minicloud-platform-docs/platform/architecture/c4-system-design) ·
**Live ArgoCD:** [argocd.devandre.sbs](https://argocd.devandre.sbs)

---

## GitOps model — the four principles, as implemented

This repo is a faithful [OpenGitOps](https://opengitops.dev) implementation — not just "YAML in Git":

| Principle | How it is implemented here |
|---|---|
| **Declarative** | Every resource is a Helm wrapper chart or raw manifest under `platform/` / `is/` — desired state, never imperative scripts. |
| **Versioned & immutable** | State lives in Git with **GPG-signed commits** + branch protection; production runs **immutable, SHA-pinned, cosign-signed images** — never `:latest`. |
| **Pulled automatically** | ArgoCD's **app-of-apps** root (`recurse: true`) discovers and pulls every `Application`. **No CI system holds cluster credentials** — the pipeline cannot push to the cluster. |
| **Continuously reconciled** | `selfHeal: true` + `prune: true` — ArgoCD detects drift and corrects it on a loop; the live cluster cannot diverge from Git. |

**The one invariant that ties it together:** *the only write path to the cluster is a merged commit.* Manual `kubectl apply`/`argocd sync` on managed workloads is forbidden — it fights self-heal — and is blocked at the keystroke by a client-side hook.

<p align="center">
  <img src="https://raw.githubusercontent.com/andrelair-platform/minicloud-platform-docs/main/static/img/architecture/platform-gitops-system.png"
       alt="GitOps workflow system — Git is the source of truth, ArgoCD is the only cluster writer" width="560" />
</p>

---

## Repository model — two pillars, separation of concerns

The layout encodes a single ownership boundary (the law is [`ARCHITECTURE.md`](ARCHITECTURE.md)):

- **`platform/`** — technical **capabilities** the platform *provides* (domain-agnostic: delivery, secrets, SSO, networking, observability, AI, data, storage).
- **`is/`** — the **Information System** that *consumes* them: the insurance business apps and the digital workplace.
- **`services/`** = *how* custom apps are packaged (Helm wrapper chart + Kargo); **`apps/`** = *where* ArgoCD classifies and deploys them.

> **Litmus test:** *if the company stopped selling insurance tomorrow, would this still exist?* **Yes → `platform/` · No → `is/`.**

| Path | Role |
|---|---|
| `bootstrap/` | The app-of-apps **seed** (`root-app.yaml`) — the only thing ever applied by hand. |
| `apps/` | ArgoCD **`Application`** manifests (the taxonomy projection): `platform/<layer>/` · `is/<group>/` · `retrieva/` · `previews/`. |
| `platform/<layer>/` | Platform capabilities by layer — `foundation` · `networking` · `secrets` · `security` · `observability` · `data` · `ai` · `delivery` · `storage` · `shared-services`. Also holds raw CRDs/policies (netpols, quotas, gatekeeper). |
| `is/<group>/` | Information-System resources — `insurance` · `erp` · `workplace`. |
| `services/<svc>/` | Per-custom-app packaging: `helm/` (GAP **wrapper chart**) + `kargo/` (promotion). **Helm-only — zero kustomize.** |
| `charts/` · `helm-values/` | The shared `minicloud-app-deployment` **library chart** (golden path) · values for third-party charts. |
| `docs/` · `.claude/` | In-repo ADRs (design coupled to code) · the agent guardrails + rules constitution. |

---

## The delivery flow — build, promote, deploy (three responsibilities, three tools)

> **CI builds & proves the artifact · Kargo promotes it · ArgoCD deploys it.** No single tool does all three — that separation is exactly what keeps the GitOps guarantee (Git is the only cluster write path) intact. Deep dive: [delivery-workflow](https://andrelair-platform.github.io/minicloud-platform-docs/platform/developer-platform/delivery-workflow).

1. **Build & prove** *(the app's own repo — never this one)* — test → build → **Trivy** scan → **cosign** keyless sign → **SBOM** → push an immutable `:<sha>` image to Harbor (dev) and ghcr (prod).
2. **Promote** *(Kargo)* — a Warehouse detects the new image → **Freight** (an immutable artifact set). Kargo auto-promotes to **dev** and runs a verification `AnalysisRun`; **only dev-verified Freight** becomes promotable to prod. Prod promotion opens a **CODEOWNERS-gated PR** — a human decides *when*. Kargo writes **Git**, never the cluster.
3. **Deploy** *(ArgoCD)* — reconciles the merged change; production rolls out as a **canary** whose analysis gate **auto-aborts** on bad metrics.

This is **continuous *deployment* to dev** (automatic) and **continuous *delivery* to prod** (human-gated) from one pipeline.

- **Environment model** — exactly **two environments** (dev + prod) running the **same artifact**; images are **env-agnostic** (config read at runtime), so dev/prod parity is *structural*, not hoped-for. Staging was deliberately removed.
- **Rollback** — `git revert` (ArgoCD reconciles the previous state) or re-promote the previous Freight. The prior state is always one commit away.

---

## Guardrails — how production stays safe (defense in depth)

No single control is trusted; a change must clear every layer. **The gate is on automation, not people** — the operator keeps documented break-glass exceptions.

| Layer | Control | What it prevents |
|---|---|---|
| **Git merge** | PR + **CODEOWNERS** (`@AndreLair`) on `apps/`, `services/*/helm`, `services/*/kargo`, `helm-values/`, `bootstrap/`, prod quotas/netpols, RBAC, and `.claude/` ; **GPG-signed** commits; branch protection | an unreviewed or unsigned change reaching prod — *this PR gate is the promotion gate* |
| **Admission** | **OPA Gatekeeper** (deny mode, 0 violations: no-privileged / no-root / no-latest / allowed-registries / resource-limits / ingress-TLS / no-hostpath / no-hostname-pin) + Pod Security Admission `restricted` | a non-compliant workload ever being admitted, even if it merged |
| **Pre-merge CI** | `validate-manifests` (**kubeconform** + `helm template`) · **checkov** · **architecture-guard** (blocks taxonomy drift) · **pr-manifest-diff** (renders the real diff on the PR) | broken manifests, structural rot, and blind merges |
| **Client-side hooks** | `.claude/hooks` deny manual `argocd sync/rollback/patch`, `kubectl delete ns`, force-push to `main`, and **secrets written to files** | mistakes caught at the keystroke, before a PR exists |
| **Audit** | one **`[CHANGE]` record** issue per prod PR (ITIL/DORA change log) | an unaccountable prod change — every one is reviewed, signed, recorded |

---

## Secrets & supply chain

- **Secrets never live in Git.** HashiCorp Vault (AWS **KMS auto-unseal**) is the source of truth; **External Secrets Operator** renders them into Kubernetes Secrets at runtime; a write-guard hook blocks committing key material.
- **Software supply chain.** Every custom image is **Trivy-scanned**, **cosign keyless-signed** (GitHub OIDC → Sigstore Fulcio) and ships a **CycloneDX SBOM** as an OCI referrer — produced in the app repo's CI. This repo deploys **only** those signed, immutable SHAs (prod → ghcr), with Gatekeeper's `allowed-registries` refusing anything else.

---

## Reconciliation, drift & observability

- **Self-heal + prune** hold the cluster exactly at Git; an out-of-band change is reverted automatically and anything removed from Git is pruned.
- **Autoscaler-aware self-heal.** Where KEDA/HPA own `.spec.replicas`, it is placed in `ignoreDifferences` with `RespectIgnoreDifferences=true` so reconciliation doesn't fight the autoscaler — the common footgun, handled.
- **Visibility.** ArgoCD surfaces per-app **Sync/Health**; Prometheus · Grafana · Loki · Tempo · OTel cover the workloads; a controller-side control-band detector (`sdlc_loop`) watches SLO bands and opens an issue on sustained breach.

---

## Disaster recovery & bootstrap

- **Rebuild from Git.** A single `kubectl apply -f bootstrap/root-app.yaml` reconstructs the entire platform through app-of-apps — the repo *is* the recovery plan.
- **State.** Velero (cluster objects + PVs), **CloudNativePG** streaming replicas with **PITR to off-site R2**, and kine/raft snapshots protect stateful data.
- **Unattended cold-start.** Vault auto-unseals via AWS KMS — a full reboot needs no human keys.

---

## The cluster

| Layer | Choice |
|---|---|
| **Kubernetes** | k3s — 6 nodes: 1 control plane (`set-hog`) + 5 workers (`fast-skunk`, `fast-heron`, `star-kitten`, `loving-gannet`, `swift-mac`) |
| **CNI / LB** | **Cilium** — CNI + LB-IPAM (`10.0.0.200`) + Hubble |
| **Identity** | Authentik — OIDC + TOTP (SSO for every app) |
| **Storage** | Longhorn (replicated: `fast-heron` / `loving-gannet` / `swift-mac`) |
| **Registry** | **Hybrid** — Harbor (dev) · ghcr.io (prod, immutable SHA, signed) |
| **AI** | LiteLLM gateway · Qdrant (RAG) · Langfuse |
| **Network** | Tailscale mesh (internal) + Cloudflare Tunnel (public `*.devandre.sbs`) |

---

<details>
<summary><b>Operate</b> — getting started · adding a service · troubleshooting</summary>

### Getting started

```bash
kubectl apply -f bootstrap/root-app.yaml                 # one-time seed; ArgoCD creates everything else
kubectl --context minicloud get applications -n argocd    # verify
```
All later changes go through **git → PR → ArgoCD**.

### Adding a new service (GAP wrapper-chart golden path)

Each custom app is its own thin Helm chart depending on the shared `minicloud-app-deployment` library (one ArgoCD source, no kustomize). Reference: `services/platform-demo/helm/` · design: [`docs/helm-golden-path.md`](docs/helm-golden-path.md).

1. Copy a reference chart (e.g. `services/platform-demo/helm/`) → `services/<name>/helm/`; `helm dependency update .` → commit `Chart.lock`.
2. Fill `values.yaml` + `values-{dev,prod}.yaml` (block-style `image.tag` — Kargo rewrites it).
3. Create the two ArgoCD `Application`s under the taxonomy home — `apps/is/<group>/` or `apps/platform/<layer>/`; keep `helm.releaseName: <name>`.
4. Add the namespaces to `platform/delivery/argocd-project/`; update the Vault k8s auth role.
5. Add a Kargo pipeline (`services/<name>/kargo/`) — promotion `yaml-update`s `minicloud-app-deployment.image.tag`.

> Validate: `cd services/<name>/helm && helm dependency update . && helm template <name> . -f values-dev.yaml`. Gotchas: [`.claude/rules/gitops.md`](.claude/rules/gitops.md).

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| App stuck syncing after Velero upgrade | `upgradeCRDs` hook Job exits 0 but k3s never sets `status.succeeded` | `upgradeCRDs: false` + `skipCrds: true` |
| Harbor sync loop / rolling restarts | `ServerSideApply: true` + `genSelfSignedCert` new checksum each render | remove `ServerSideApply: true` from the Harbor app |
| Webhook pod `connection refused` | under Cilium an `ipBlock` CIDR doesn't match the apiserver identity | CiliumNetworkPolicy `toEntities: [kube-apiserver, host, remote-node]` |
| Kargo promotion `Error` on image bump | `image.tag` written in flow style `{ tag: … }` | block-style YAML in `values-*.yaml` |
| ESO `SecretSyncedError` | Vault KV path changed / policy missing `read` | check `vault kv get secret/platform/<name>` + the k8s-auth role namespaces |

</details>

---

## Related repos & meta

[minicloud-ansible](https://github.com/andrelair-platform/minicloud-ansible) (k3s bootstrap) ·
[minicloud-opentofu](https://github.com/andrelair-platform/minicloud-opentofu) (MAAS IaC) ·
[minicloud-backstage](https://github.com/andrelair-platform/minicloud-backstage) ·
[minicloud-platform-docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[minicloud-litellm-custom](https://github.com/andrelair-platform/minicloud-litellm-custom) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo)

`tech-radar.json` (root) feeds the Backstage [Tech Radar](https://backstage.devandre.sbs/tech-radar) live. Releases via release-please; deps via Renovate.

## License

[MIT](LICENSE) © andrelair-platform
