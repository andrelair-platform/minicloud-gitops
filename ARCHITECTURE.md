# minicloud-gitops — Architecture (canonical repository contract)

> **This file is the law for where things live in this repo.** It is the human map; the enforced decision
> rule is `.claude/rules/platform-vs-information-system.md`; the migration that establishes this layout is
> `docs/remediation-plan.md` (diagnosis: `docs/architecture-audit.md`). Discoverable summary on the hub:
> [Repository taxonomy contract](https://andrelair-platform.github.io/minicloud-platform-docs/platform/architecture/repo-taxonomy-contract).

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
platform/                  # (cluster-scoped resources live WITHIN a layer: quotas → security/quotas,
                           #  storage classes → storage/, netpols → security/network-policies — there is
                           #  no separate clusters/ dir)
  foundation/              # cilium, cert-manager, kured, vpa, system-upgrade, priority
  storage/                 # longhorn, external-snapshotter, backup-dr (velero + CNPG backups)
  networking/              # ingress-nginx, external-dns, cloudflare-tunnel, metallb
  secrets/                 # vault, external-secrets
  delivery/                # argocd, argo-rollouts, kargo, harbor
  security/                # gatekeeper-policies, network-policies, falco, rbac, polaris, quotas
  observability/           # kube-prometheus-stack, grafana, loki, tempo, otelcol, monitoring
  data/                    # CNPG operator + shared data engine (kafka/clickhouse)   [per-app DBs stay with the app]
  automation/              # temporal (durable, code-first workflow/orchestration engine)
  ai/                      # litellm, qdrant, langfuse(+base), open-webui
  shared-services/         # authentik(+ldap-outpost, cnpg-authentik), adminer, homer, ghproj-exporter,
                           #   nats (shared eventing bus), keda (event/metric-driven scaling)
  _demos/                  # non-prod examples/validation: whoami, podinfo, event-demo, chaos-engineering
                           #   (sanctioned, kept — all live/Synced; a working demo of a path, not a 1st-class layer)
is/                        # raw/vendor IS manifests (custom IS services live in services/, deployed via apps/is/)
  workplace/               # nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden
  erp/                     # erpnext
  insurance/               # raw/vendor LOB bundles (custom LOB services stay in services/)
                           #   NB iam (ktayl-iam) + itsm (glpi/ktayl-itsm) are custom SERVICES → services/,
                           #   with their Application files under apps/is/{iam,itsm}; not raw is/ subdirs.
services/                  # custom wrapper charts (+ /kargo) — UNCHANGED, flat, packaging only
apps/
  platform/{foundation,storage,networking,secrets,delivery,security,observability,data,automation,ai,shared-services,_demos}/
  is/{workplace,iam,erp,insurance,itsm}/
  retrieva/                # RNCP39583 cert product's Application files (neither platform/ nor is/ — §14)
  previews/
helm-values/ · charts/                         # UNCHANGED  (environments/ retired 2026-11-13 — unused)
docs/ · scripts/ · .claude/ · ARCHITECTURE.md
```

## Per-directory contract

| Dir | Purpose | Allowed | Forbidden | Owner |
|---|---|---|---|---|
| `platform/*` | shared technical capabilities (incl. cluster-scoped resources within a layer — quotas → `security/quotas`, SCs → `storage/`) | infra/delivery/secrets/obs/security/data-engine/ai/shared-svc + ns/quota/limitrange/cluster-RBAC/SC | **any business/IS app** | Platform Eng |
| `is/*` | business apps/data (consumers) | workplace/ERP/LOB/ITSM/data products | **platform infra**, **app source code** | App/Domain |
| `services/` | packaging of custom-built services | wrapper charts + `/kargo` | vendor charts, raw infra | Platform Eng |
| `apps/` | Argo CD Applications (taxonomy) | Application/ApplicationSet/AppProject under `platform/*`, `is/*`, `retrieva/` (cert product) or `previews/` | workload manifests; `apps/workloads/` (retired) | Platform Eng |

## Canonical homes for ambiguous components (deterministic placement, not philosophical perfection)

Harbor → `platform/delivery/` · external-snapshotter → `platform/storage/` · Polaris → `platform/security/` ·
backup-dr → `platform/storage/` · cnpg-authentik (Authentik's DB) → `platform/shared-services/` ·
langfuse-base → `platform/ai/` · CNPG **operator** → `platform/data/` (per-app CNPG clusters stay with their app).
*If a future component is genuinely 50/50, add a line here instead of debating it in a PR.*

**Automation boundary (Temporal vs n8n — different problems, different pillars):**
`platform/automation` = **automation *infrastructure*** (Temporal: durable, code-first workflow execution
for services — retries, state, long-running, compensation → *"how do our systems reliably execute
workflows?"*). `is/` = **business process automation** (n8n: low-code, business/IT users connecting apps —
onboarding, approvals, notifications, document routing → *"how do teams automate business processes?"*).
n8n stays IS (currently `is/workplace/n8n`; promote to `is/automation/` if it grows into a broad business-automation surface).

## FREEZE (in force — enforced, Stage 6)

- **`manifests/` is fully migrated and GONE** (LOT E, 2026-10 — PRs #1780–1782 moved every dir to
  `platform/<layer>/`). The FREEZE succeeded: new config goes to `platform/<layer>/` or `is/<group>/`,
  **never** a recreated `manifests/`. (The guard-write hook + architecture-guard CI still refuse a new
  `manifests/<subdir>` — now a belt-and-braces guard against the dir ever coming back.)
- **`apps/platform/` (flat) is FROZEN** — new Argo Applications go under `apps/platform/<layer>/` or `apps/is/<group>/`.
- A **new top-level directory requires an ADR.**
- **No application source code in this repo** — code lives in the product repo; a runtime Job clones it.

> **Enforced on two layers (remediation-plan.md Stage 6):** the agent-layer hook
> `.claude/hooks/guard-write.py` (rules 5–6, keystroke-time) **and** the server-side CI check
> `.github/workflows/architecture-guard.yml` (every PR). Both inspect only *new* entries
> (creation / PR-added files) so any remaining legacy residue (e.g. the emptied `apps/workloads/`) is
> grandfathered — the FREEZE blocks adding to the entropy, not the existing state.

## Migration invariant (every refactor PR)

> **Note — the taxonomy refactor is COMPLETE** (manifests/ fully migrated, 2026-10). The three sections
> below — Migration invariant · Non-regression oracle · Scope guardrails — are the **playbook that was
> run**, kept as the historical record + the pattern for any *future* path refactor. They are not a
> live-work queue. The **two pillars + FREEZE above remain in force.**

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
