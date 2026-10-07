# minicloud-gitops — Architecture (canonical repository contract)

> **This file is the law for where things live in this repo.** It is the human map; the enforced decision
> rule is `.claude/rules/platform-vs-information-system.md`; the migration that establishes this layout is
> `docs/remediation-plan.md` (diagnosis: `docs/architecture-audit.md`).

## The two pillars (the one boundary that must never blur)

```
platform/   → What technical capabilities does the platform PROVIDE?   (domain-agnostic)
is/         → What belongs to the Information System / insurance business?  (the CONSUMERS)
services/   → HOW are custom-built applications packaged?  (wrapper charts + Kargo — PACKAGING, not taxonomy)
apps/       → WHERE does Argo CD classify and deploy everything?  (the taxonomy projection)
```

**The litmus test for every new component:**
> *If the company stopped selling insurance tomorrow, would this still have a reason to exist?*
> **Yes → `platform/<layer>/`**  ·  **No → `is/<group>/`**

## Canonical tree

```
bootstrap/                 # root app-of-apps only
clusters/minicloud-1/      # cluster-scoped: namespaces, quotas, limitranges, cluster RBAC, storage classes
platform/
  foundation/              # cilium, cert-manager, kured, vpa, system-upgrade, priority
  storage/                 # longhorn, external-snapshotter, backup-dr (velero + CNPG backups)
  networking/              # ingress-nginx, external-dns, cloudflare-tunnel, metallb
  secrets/                 # vault, external-secrets
  delivery/                # argocd, argo-rollouts, kargo, harbor
  security/                # gatekeeper-policies, network-policies, falco, rbac, polaris, quotas
  observability/           # kube-prometheus-stack, grafana, loki, tempo, otelcol, monitoring
  data/                    # CNPG operator + shared data engine (kafka/clickhouse)   [per-app DBs stay with the app]
  ai/                      # litellm, qdrant, langfuse(+base), open-webui
  shared-services/         # authentik(+ldap-outpost, cnpg-authentik), adminer, homer, ghproj-exporter
is/
  workplace/               # nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden
  iam/                     # ktayl-iam (Identity & Access Governance / IGA — transverse IS capability)
  erp/                     # erpnext
  insurance/               # raw/vendor LOB bundles (custom LOB services stay in services/)
  itsm/                    # glpi
  data-products/           # policy_portfolio / metabase provisioning CONFIG (code in ktayl-data-platform)
services/                  # custom wrapper charts (+ /kargo) — UNCHANGED, flat, packaging only
apps/
  platform/{foundation,storage,networking,secrets,delivery,security,observability,data,ai,shared-services}/
  is/{workplace,iam,erp,insurance,itsm,data-products}/
  previews/
helm-values/ · charts/ · environments/        # UNCHANGED
docs/ · scripts/ · .claude/ · ARCHITECTURE.md
```

## Per-directory contract

| Dir | Purpose | Allowed | Forbidden | Owner |
|---|---|---|---|---|
| `clusters/` | cluster-scoped bootstrap | ns, quota, limitrange, cluster RBAC, SC | app workloads | Platform/SRE |
| `platform/*` | shared technical capabilities | infra/delivery/secrets/obs/security/data-engine/ai/shared-svc | **any business/IS app** | Platform Eng |
| `is/*` | business apps/data (consumers) | workplace/ERP/LOB/ITSM/data products | **platform infra**, **app source code** | App/Domain |
| `services/` | packaging of custom-built services | wrapper charts + `/kargo` | vendor charts, raw infra | Platform Eng |
| `apps/` | Argo CD Applications (taxonomy) | Application/ApplicationSet/AppProject under `platform/*` or `is/*` | workload manifests | Platform Eng |
| `environments/` | per-env config | values, quota, limitrange, namespace | app definitions | Platform + env |

## Canonical homes for ambiguous components (deterministic placement, not philosophical perfection)

Harbor → `platform/delivery/` · external-snapshotter → `platform/storage/` · Polaris → `platform/security/` ·
backup-dr → `platform/storage/` · cnpg-authentik (Authentik's DB) → `platform/shared-services/` ·
langfuse-base → `platform/ai/` · CNPG **operator** → `platform/data/` (per-app CNPG clusters stay with their app).
*If a future component is genuinely 50/50, add a line here instead of debating it in a PR.*

## FREEZE (in force)

- **`manifests/` is FROZEN** — no new subdirectories. New config goes to `platform/<layer>/` or `is/<group>/`.
- **`apps/platform/` (flat) is FROZEN** — new Argo Applications go under `apps/platform/<layer>/` or `apps/is/<group>/`.
- A **new top-level directory requires an ADR.**
- **No application source code in this repo** — code lives in the product repo; a runtime Job clones it.

## Migration invariant (every refactor PR)

A refactor PR changes **paths only**. **Do NOT** change simultaneously: `metadata.name`, namespace, Helm
values, chart contents, Kubernetes resources, image versions, or any configuration.

```
git mv  →  update spec.source.path  →  argocd app diff EMPTY  →  merge  →  Synced + Healthy
```
If the Argo diff is not empty for a component, **stop and investigate that component.**

## Non-regression oracle (baseline 2026-10-07)

The cluster is **not all-green** independently of this refactor. The pre-existing NOT-`Synced/Healthy` set is:

```
root, langfuse, langfuse-base, litellm, monitoring-dashboards, ktayl-claims-dev,
ktayl-iam-prod, minicloud-plane-dev, kargo-ktayl-policy-service, kargo-ktayl-underwriting
```

**The oracle is therefore "do not ADD to this set"**, not "everything is green". After each migration PR,
confirm the moved app is `Synced/Healthy` and that no *new* app left this baseline set. (These 10 are
pre-existing drift/health issues, out of scope for the taxonomy refactor.)

## Scope guardrails (the four hard do-nots)

Do **not** split the repo · do **not** redesign GitOps · do **not** rename namespaces · do **not** touch the
deployment engine. This is a controlled **taxonomy / path refactor** only.
