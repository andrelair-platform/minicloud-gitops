# minicloud-gitops — Deep Architectural Audit

> Read-only architecture audit (no files modified during the audit). Performed as a Senior Platform /
> Kubernetes / GitOps / SRE review. Date: 2026-10-07.

## 1. Executive Summary

**The GitOps *machinery* is mature and genuinely good; the *organization of the filesystem* is where it has decayed.** You have a clean helm-only model (0 `kustomization.yaml`, 26 charts), a correct app-of-apps (`bootstrap/root-app.yaml` → `apps/` recurse), a working 2-env + Kargo promotion model, a shared library chart (`charts/minicloud-app-deployment`), ESO/Vault, sync-waves, and a documented wrapper-chart golden path. These are senior-grade.

The problem is **two giant flat catch-alls**:
- **`manifests/` = 55 sibling subdirectories (~426 files)** mixing *every* concern — CNI, storage, security policy, observability, data, AI, and ~15 business/IS applications — with **no layer separation whatsoever**.
- **`apps/platform/` = 66 ArgoCD Applications** defined as "everything that isn't a workload," so true platform infra (Cilium, ESO, cert-manager, Argo) sits next to shared services (Harbor) and **business apps (BookStack, Adminer)** and even `kargo-retrieva`.

Ironically, this session fixed exactly this *mixture* on the **docs site** and wrote a rule (`platform-vs-information-system.md`) demanding a strict Platform↔IS boundary — **but the deployment repo's filesystem does not embody that rule.** The docs now separate Platform from IS; the manifests do not.

**Severity:** nothing is **P0 (dangerous)** — the platform runs, env separation is sound, no reliability threat. The findings are **P1 (structural)** and **P2/P3 (maintainability)**. This is mostly *"structurally ugly but operationally valid,"* with a handful of *genuinely wrong* items (stray application code in the repo, the arbitrary platform/workloads split, namespace inconsistency).

**Verdict up front:** Keep **one** GitOps repo. Do **not** split. **Reorganize internally** into explicit layers that encode the Platform↔IS boundary you already made canonical. This is a filesystem/convention refactor, not an architecture rewrite.

---

## 2. Current Repository Architecture (as actually assembled)

```
bootstrap/root-app.yaml      ← app-of-apps: Application "root", path: apps, recurse: true
        │  (prune + selfHeal + CreateNamespace + ServerSideApply)
        ▼
apps/                        ← one ArgoCD Application per file, discovered by recursion
  ├── platform/   (66 files) ← "everything not a workload": infra + shared svc + security + SOME business
  │     + environments.yaml  (ApplicationSet → environments/overlays/*)
  │     + kargo-projects.yaml (ApplicationSet → services/*/kargo)
  ├── workloads/  (39 files) ← deployed apps: IS business + AI platform + demos, dev & prod as separate files
  └── previews/   (1)        ← preview env (PR apps)

Each Application's source is ONE of:
  • path: manifests/<x>          (55 apps)  raw-CR bundle (.Files.Get packaging chart) OR plain manifests
  • path: services/<x>/helm      (22 apps)  GAP wrapper chart (custom-built services + Kargo)
  • remote chart + helm-values/  (37 apps)  third-party vendor charts

Supporting trees:
  charts/minicloud-app-deployment   the shared library chart (good)
  helm-values/minicloud-1/ (38)     third-party chart values
  environments/overlays/{dev,prod}/{collab,insurance}   ns + quota + limitrange (+dev rolebinding)
  docs/ (26 ADRs) · bmad/ (stories) · evals/ · intent/ · scripts/ · images/ · .claude/ (rules+hooks)
  data-platform/metabase/provision_dashboard.py   ← ⚠ stray application code
```

**Facts verified:** 812 YAML files · **0 `kustomization.yaml`** (helm-only ✅) · 26 `Chart.yaml` · 2 ApplicationSets · sync-waves used in 55 files (range −3…+2) · env model = `values-dev.yaml`/`values-prod.yaml` + Kargo (no manifest duplication).

---

## 3. Current Architectural Map

```
Cluster (k3s, minicloud-1)
│
├── Foundation            [scattered in manifests/ + apps/platform]
│   ├── Cilium (+wireguard, hubble)      manifests/cilium
│   ├── Longhorn (+ longhorn-base app)   manifests/longhorn
│   ├── cert-manager / cert-manager-config
│   ├── external-snapshotter, system-upgrade, kured, vpa, priority(class), rbac
│
├── Platform infra        [scattered in manifests/ + apps/platform]
│   ├── Argo CD / argo-rollouts          (self-managed)
│   ├── Vault + External Secrets (ESO)   manifests/vault, eso-platform-secrets
│   ├── ingress-nginx, external-dns, cloudflare-tunnel
│   └── CNPG operator (cloudnative-pg), Kargo
│
├── Platform / shared services
│   ├── Authentik (+ ldap-outpost, cnpg-authentik)
│   ├── Harbor, Adminer, Homer, ghproj-exporter
│
├── Observability          manifests/monitoring, loki, otelcol, tempo  + Grafana/Prometheus (helm-values)
├── Security               gatekeeper-policies, network-policies(52!), polaris, falco
├── AI platform            manifests/ai (LiteLLM/Qdrant/seeder) + workloads: litellm, langfuse, open-webui
├── Data platform          manifests/data-platform (pipeline clones ktayl-data-platform), langfuse-base
│
└── Business / IS (ktayl-solution)   ← MIXED INTO manifests/ + apps/workloads + apps/platform
    ├── Digital Workplace: nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden
    ├── ERP: erpnext
    ├── Insurance LOB: services/ktayl-{claims,iam,itsm,policy-service,underwriting} + ktayl-core(-infra) + ktayl(-base)
    └── Project mgmt: plane / minicloud-plane
```

The map is coherent *conceptually* — but it is a **reconstruction**; the filesystem does not express these layers. Everything is flattened into `manifests/` and `apps/{platform,workloads}`.

---

## 4. Classification of Components

Applying the `platform-vs-information-system.md` litmus (*"survives if ktayl stops selling insurance?"*):

| Category | Components (in repo) | Survives? → Layer |
|---|---|---|
| **Cluster Foundation** | cilium, longhorn, cert-manager(-config), external-snapshotter, system-upgrade, kured, vpa, priority, rbac, external-dns | Yes → **Platform** |
| **Platform Infra / Delivery** | argocd(+rollouts), vault, eso-platform-secrets, cnpg operator, kargo, ingress-nginx, cloudflare-tunnel, harbor | Yes → **Platform** |
| **Platform Shared Services** | authentik(+ldap-outpost, cnpg-authentik), adminer, homer, ghproj-exporter | Yes → **Platform** |
| **Observability** | monitoring, loki, otelcol, tempo, polaris | Yes → **Platform** |
| **Security** | gatekeeper-policies, network-policies, falco, quotas, cert-observability | Yes → **Platform** |
| **AI Platform** | ai/ (litellm/qdrant/seeder), langfuse(-base), open-webui | Yes → **Platform** |
| **Data Platform (engine)** | cnpg operator, kafka/clickhouse (planned), data-platform *pipeline infra* | Yes → **Platform** |
| **Business / IS — Digital Workplace** | nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden | No → **IS** |
| **Business / IS — ERP & LOB** | erpnext, ktayl-{claims,iam,itsm,policy-service,underwriting}, ktayl-core, plane | No → **IS** |
| **IS data *products*** | data-platform `policy_portfolio` / metabase provisioning | No → **IS** |
| **Environment config** | environments/overlays/{dev,prod}/{collab,insurance} | → **Environment** |
| **Repo-ops / meta** | docs, bmad, evals, intent, scripts, .claude, catalog-info, tech-radar | → **Repo meta** |
| **Stray code (misfiled)** | `data-platform/metabase/provision_dashboard.py` | **belongs in `ktayl-data-platform` repo** |

The classification is clean **conceptually**; the repo places ~11 of these 13 categories into **one flat `manifests/`**.

---

## 5. What Is Already Well Structured (don't touch)

1. **Helm-only, no kustomize** (0 `kustomization.yaml`) — a decisive, consistent modeling choice. ✅
2. **App-of-apps** via `bootstrap/root-app.yaml` + recurse — simple and standard. ✅
3. **The GAP wrapper-chart golden path** (`services/<svc>/helm` + `charts/minicloud-app-deployment` library) — this is genuinely senior; 22 apps use it consistently. ✅
4. **Environment separation is correct** — `values-dev.yaml`/`values-prod.yaml` + Kargo promotion + separate dev/prod Application files. **No manifest duplication.** This is the textbook-right answer. ✅
5. **The 3 packaging patterns are a deliberate, documented taxonomy** (raw `.Files.Get` bundle / GAP wrapper chart / vendor chart + `helm-values`). *This looks mixed but is correct* (see §19 Q4).
6. **ESO + ArgoCD SSA `ignoreDifferences`**, Kargo ApplicationSet auto-discovery, sync-waves present. ✅
7. **ADRs in `docs/` + the `.claude/rules` constitution + hooks** — the repo documents and *enforces* its own conventions. ✅ (The irony: the rules are ahead of the filesystem.)

---

## 6. Separation-of-Concerns Problems

| # | Problem | Evidence |
|---|---|---|
| S1 | **`manifests/` is a 55-dir catch-all with no layering** | foundation (cilium), security (gatekeeper-policies), observability (monitoring), data (cnpg-authentik), AI (ai), and business (nextcloud, erpnext, matrix, stalwart, bookstack…) are all direct siblings |
| S2 | **`apps/platform/` = "not-a-workload" grab bag** | 66 Applications: cilium + eso + cert-manager next to bookstack, adminer, kargo-retrieva |
| S3 | **The platform/workloads split is arbitrary** | nextcloud/stalwart/erpnext are `apps/workloads/`, but bookstack/adminer/homer are `apps/platform/` — all are IS/shared apps. No consistent rule distinguishes them |
| S4 | **IS business apps are not grouped** | no `is/`, `domains/`, or `business/` tree — the exact mixture just removed from the docs site persists in the manifests |
| S5 | **Namespace naming mixes three schemes** | technical (`cert-manager`,`ingress-nginx`,`keda`) + business domain (`claims`,`erp`,`itsm`,`ktayl-core`) + **env-in-namespace** (`claims-prod`,`ktayl-prod`,`ktayl-iam-prod`) — inconsistent env encoding |

---

## 7. Misplaced Components

| Component | Current | Should be |
|---|---|---|
| `data-platform/metabase/provision_dashboard.py` | repo root (top-level `data-platform/`) | **`ktayl-data-platform` repo** — it's application code; the repo-vs-code rule (conventions.md) was "fixed 2026-09-27" but this file regressed it |
| `bookstack`, `adminer`, `homer` (apps) | `apps/platform/` | IS/shared-services layer (they're user-facing apps, not platform infra) |
| `kargo-retrieva` (app) | `apps/platform/` | Retrieva is a **cert product** (own docs/repo) — its Kargo app sits oddly among platform infra |
| `manifests/langfuse-base`, `cnpg-authentik` | flat in `manifests/` | data/AI-platform sub-layer |
| `services/_template-helm` | `services/` | a scaffold — `gitops.md` claims the `_template` scaffold was removed; it wasn't |

---

## 8. Platform vs Application Boundary Problems

This is the **central finding** and it maps 1:1 to the rule authored this session.

- The repo has **no filesystem boundary** between *capabilities* (Platform) and *business use* (IS). Both live in `manifests/` and both are "Applications" in `apps/`.
- **Dependency direction is actually correct** at runtime (business apps → platform capabilities, not the reverse) — **no `platform → business` inversion** was found. The problem is **expression**, not direction: you cannot *see* the boundary, so new contributors (and future-you) drop new services into whichever flat dir is handy → entropy compounds.
- **The one real leak**: a business data-product provisioner (`provision_dashboard.py`) living in the platform/GitOps repo.

**Looks-mixed-but-correct (do NOT "fix"):** Authentik, Vault, CNPG, the AI gateway serving business workloads is **not** a boundary violation — those are Platform capabilities being *consumed* by IS, which is exactly right.

---

## 9. Environment Structure Problems

Mostly **healthy**. One real inconsistency:

- **Env encoded two different ways.** Most services: one artifact promoted dev→prod via `values-{dev,prod}.yaml` + Kargo (✅ correct). But some namespaces bake env into the **namespace name** (`claims-prod`, `ktayl-prod`, `ktayl-iam-prod`) while `environments/overlays/` encodes env as a **path dimension** (`dev/`,`prod/`). Pick one convention. (P2)
- `environments/overlays/{dev,prod}/{collab,insurance}` for only ns+quota+limitrange is **mild over-abstraction** (4 near-identical `.Files.Get` charts; dev adds a rolebinding). Acceptable, but it's 4 charts to express ~12 small objects. (P3)

No harmful dev/prod manifest duplication was found. ✅

---

## 10. GitOps / Argo CD Architecture Findings

- **App-of-apps via blind recursion** (`path: apps`, `recurse: true`) means ArgoCD creates ~106 Applications **flat**, with no declared layer grouping. Sync-waves exist (55 files, −3…+2) so *ordering* is partially handled, but there is **no structural "foundation → platform → services → domains" app hierarchy** — ordering is an afterthought annotation, not an architecture. (P2)
- **`apps/platform/` conflates the ArgoCD *project* question with the *layer* question.** You have `argocd-project` + AppProjects, but the app *files* aren't organized by project/layer.
- **Two ApplicationSets** (`environments`, `kargo-projects`) are good, contained uses. ✅
- **Risk:** because `apps/platform/` is the default dumping ground, a business app added there inherits platform sync-policy/placement assumptions silently.

---

## 11. Security / Networking / Storage / Observability Findings

- **Security: strong.** 52 network-policies, 29 gatekeeper-policies, falco, polaris, quotas, ESO/Vault. The *content* is senior-grade. The *placement* (flat in `manifests/`) is the only issue. Policies are split (`gatekeeper-policies/`, `network-policies/`, `rbac/`, `quotas/`) — consider a single `policies/` layer. (P3)
- **Networking:** cilium (+wireguard/hubble), metallb, ingress-nginx, external-dns, cloudflare-tunnel — all present, correct layer, just flat. ✅ content.
  - **Ingress controller = the COMMUNITY `ingress-nginx`** (chart `kubernetes.github.io/ingress-nginx`, image `registry.k8s.io/ingress-nginx`, `nginx.ingress.kubernetes.io/*` annotations, `ingressClassName: nginx`, 0 `VirtualServer` CRDs) — **not** the F5/NGINX-Inc "NGINX Ingress Controller". Two naming smells (P3): (a) the app/values files are named `nginx-ingress*` (the F5-style name) though they deploy the community `ingress-nginx` → rename to `ingress-nginx*`; (b) a comment in `argocd-values.yaml` warned against the **F5** annotation `nginx.org/proxy-buffer-size` (a no-op on this controller) when the real reload-breaking annotation is the **community** `nginx.ingress.kubernetes.io/proxy-buffer-size` → comment corrected. Risk: following F5 docs (VirtualServer / `nginx.org/*` / JWT Policy) silently no-ops here.
- **Storage:** Longhorn + external-snapshotter + backup-dr + CNPG. Note `longhorn-base` (workloads) + `manifests/longhorn` + backup split across dirs — storage concern is scattered across 3 locations. (P2)
- **Observability: strong but scattered** across `monitoring/`, `loki/`, `otelcol/`, `tempo/`, `polaris/`. `40-dora-dashboard` + `ghproj-exporter` are **platform/delivery** dashboards (correct — *not* business dashboards; verified). No business-dashboard-in-platform smell found. ✅

---

## 12. Repository Boundary Analysis

**Is the repo doing too much?** Slightly, but defensibly. It holds: deployment config (correct) + `bmad/` stories + `docs/` ADRs + `evals/` + `intent/` + `.claude/` + **stray app code**.

| Model | Pros | Cons |
|---|---|---|
| **Monorepo GitOps (today)** | one sync root, atomic cross-cutting changes, one CODEOWNERS gate, trivial to reason about for a solo operator, no cross-repo version skew | the flat catch-alls hide structure; CODEOWNERS can't express per-layer ownership well |
| **Multi-repo** (`-infrastructure`/`-platform`/`-applications`/`-policies`) | per-layer ownership + RBAC, independent blast radius, cleaner mental model | N× sync roots, cross-repo ordering, version skew, massive overhead for **one operator** |

**Recommendation for *today* (a solo-operated platform): KEEP ONE REPO.** Multi-repo solves a *team-ownership* problem you don't have, at a real coordination cost. **Get the layering right *inside* the monorepo first** — that captures 90% of the benefit with none of the overhead. Only evict: the **stray `data-platform/` code** → `ktayl-data-platform`. Revisit splitting **only** if a second human owns "platform" vs "applications."

---

## 13. Proposed Target Architecture

A **layer-first** top level that encodes Platform↔IS and foundation→domain ordering. `apps/` mirrors the layers instead of platform/workloads.

```
bootstrap/                 # root app-of-apps only
clusters/minicloud-1/      # cluster-scoped: namespaces, quotas, limitranges, cluster RBAC, storageclasses
platform/
  foundation/              # cilium, longhorn, cert-manager, external-snapshotter, kured, vpa, system-upgrade
  delivery/                # argocd, argo-rollouts, kargo
  secrets/                 # vault, eso
  networking/              # ingress-nginx, external-dns, cloudflare-tunnel, metallb
  observability/           # prometheus, grafana, loki, tempo, otelcol, polaris, dora/ghproj
  security/                # gatekeeper-policies, network-policies, falco   (or top-level policies/)
  data/                    # cnpg operator, kafka/clickhouse engine, (data-platform PIPELINE infra)
  ai/                      # litellm, qdrant, langfuse, open-webui
  shared-services/         # harbor, authentik(+ldap-outpost), adminer, homer, ghproj-exporter
is/                        # ← the Information System (business)
  workplace/               # nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden
  erp/                     # erpnext
  domains/                 # ktayl-claims, ktayl-iam, ktayl-underwriting, ktayl-policy-service, ktayl-itsm, ktayl-core
  data-products/           # policy_portfolio / metabase provisioning CONFIG (code stays in ktayl-data-platform)
environments/              # dev/prod overlays (values + quota/limitrange per env)
apps/                      # ArgoCD Applications, organized to MIRROR the layers above (+ ApplicationSets)
  platform/{foundation,delivery,…}/   is/{workplace,domains,…}/
policies/                  # (optional) if you prefer policies as a first-class layer
charts/                    # shared library chart(s)
docs/ · bmad/ · .claude/   # repo meta (unchanged)
```

Per top-level dir:

| Dir | Purpose | Allowed | Forbidden | Owner | Lifecycle | Scope |
|---|---|---|---|---|---|---|
| `clusters/` | cluster-scoped bootstrap objects | ns, quota, limitrange, cluster RBAC, SC | app workloads | Platform/SRE | cluster | cluster |
| `platform/*` | shared technical capabilities | infra, delivery, secrets, obs, security, data engine, AI, shared svc | **any business/IS app** | Platform Eng | platform | platform/ns |
| `is/*` | business apps/data (consumers) | workplace, ERP, LOB domains, data products | **platform infra**, app source code | App/Domain teams | app/business | ns |
| `environments/` | per-env config only | values, quota, limitrange, namespace | app definitions | Platform + env owner | environment | env |
| `apps/` | ArgoCD Applications, mirroring layers | Application/ApplicationSet/AppProject | actual workload manifests | Platform Eng | GitOps | n/a |
| `policies/` | admission/network/security policy | Gatekeeper, netpol, RBAC | app config | Security | platform | cluster/ns |

---

## 14. Current vs Target Directory Tree

```
CURRENT                                   TARGET
───────                                   ──────
bootstrap/root-app.yaml                   bootstrap/root-app.yaml
apps/                                      apps/
  platform/  (66, mixed) ───────────────▶   platform/{foundation,delivery,secrets,networking,
  workloads/ (39, mixed) ───────────────▶            observability,security,data,ai,shared-services}/
  previews/                                  is/{workplace,erp,domains,data-products}/
                                             previews/
manifests/  (55 flat dirs) ─── split ──▶  platform/<layer>/<component>/   AND   is/<group>/<app>/
  cilium, longhorn, cert-manager… ──────▶   platform/foundation/
  gatekeeper-policies, network-policies ─▶  platform/security/ (or policies/)
  monitoring, loki, otelcol, tempo ─────▶   platform/observability/
  ai, langfuse-base ────────────────────▶   platform/ai/
  cnpg-authentik, data-platform ────────▶   platform/data/   (+ is/data-products for the product config)
  harbor, adminer, homer, ghproj ───────▶   platform/shared-services/
  nextcloud, stalwart, matrix, jitsi,                is/workplace/
    docuseal, n8n, bookstack, searxng,  ─▶
    vaultwarden
  erpnext ──────────────────────────────▶   is/erp/
  ktayl, ktayl-core, plane ─────────────▶   is/domains/
services/<svc>/helm        (KEEP) ────────▶ services/<svc>/helm            (unchanged, reference pattern)
charts/minicloud-app-deployment (KEEP) ──▶ charts/                        (unchanged)
helm-values/minicloud-1/   (KEEP) ────────▶ helm-values/minicloud-1/       (unchanged; or co-locate per layer later)
environments/overlays/…    (KEEP) ────────▶ environments/                  (unchanged)
data-platform/metabase/provision_dashboard.py  ──── EVICT ──▶ ktayl-data-platform repo
services/_template-helm    ──── DELETE (dead scaffold)
```

---

## 15. Architecture Scorecard

| Area | Score | Why |
|---|---:|---|
| Separation of concerns | **4/10** | Correct *conceptually*, but `manifests/` + `apps/platform/` are flat catch-alls; no filesystem boundary between layers or Platform↔IS |
| Platform/application boundary | **4/10** | Runtime dependency direction is correct (no inversion), but the boundary is **invisible** in the tree; 1 real leak (stray code) |
| Environment separation | **9/10** | 2-env, values-dev/prod + Kargo, no manifest duplication — exemplary; −1 for env-in-namespace inconsistency |
| GitOps architecture | **7/10** | app-of-apps + ApplicationSets + Kargo + sync-waves are solid; −3 for flat recursion with no layer hierarchy |
| Directory structure | **4/10** | 55 flat `manifests/` dirs + arbitrary platform/workloads split |
| Dependency management | **7/10** | sync-waves + AppProjects + ESO ignoreDifferences present; ordering is sparse/implicit, not structural |
| Security architecture | **8/10** | Gatekeeper + 52 netpols + Falco + ESO/Vault + quotas — strong; −2 for scattered policy placement |
| Observability architecture | **8/10** | full Prom/Graf/Loki/Tempo/OTel + DORA + exporters; −2 for scatter across 5 dirs |
| Storage/data architecture | **7/10** | Longhorn + CNPG + snapshots + backup-dr + the CNPG standard; −3 for storage scattered across 3 locations + data-product code leak |
| Maintainability | **5/10** | Great rules/ADRs, but catch-alls mean "where does X go?" has no deterministic answer → entropy |
| Scalability | **6/10** | Mechanics scale (wrapper chart, Kargo); the flat org does not — `manifests/` will hit 100+ dirs |
| Developer experience | **5/10** | Strong golden path for *new custom services*; poor for *finding/placing* anything in the flat trees |

**Weighted read: ~6/10 — a strong engine in a disorganized chassis.**

---

## 16. Prioritized Findings

| Finding | Current location | Expected responsibility | Why problematic | Sev | Recommendation | Destination | Migration |
|---|---|---|---|---|---|---|---|
| `manifests/` is a 55-dir catch-all | `manifests/` | layered platform/IS config | no deterministic "where does X go"; entropy compounds | **P1** | split by layer (Platform vs IS vs policies) | `platform/*`, `is/*` | **High** |
| `apps/platform/` = not-a-workload grab bag | `apps/platform/` | ArgoCD apps grouped by layer | business apps inherit platform assumptions; split is arbitrary | **P1** | mirror layers under `apps/` | `apps/{platform,is}/*` | **High** |
| Business/IS apps not grouped | `manifests/` + `apps/workloads` | an `is/` tree | the mixture the new rule forbids | **P1** | introduce `is/{workplace,erp,domains}` | `is/*` | Medium |
| Stray application code in repo | `data-platform/metabase/provision_dashboard.py` | code → product repo | violates deploy-repo≠code-repo (a regressed rule) | **P1** | move to `ktayl-data-platform`; deployment clones it | code repo | **Low** |
| Env encoded two ways | namespaces `*-prod` vs `environments/overlays` | one env convention | inconsistent mental model | P2 | standardize (prefer overlay/values, not ns-suffix) | — | Medium |
| Storage concern scattered | `longhorn`, `longhorn-base`, `backup-dr` | one storage layer | hard to reason about storage holistically | P2 | `platform/foundation/storage/*` | — | Low |
| Policies split 4 ways | gatekeeper/netpol/rbac/quotas | one policy layer | fragmented security ownership | P3 | `policies/` (or `platform/security/`) | — | Low |
| `_template-helm` dead scaffold | `services/_template-helm` | — | rule says removed; it isn't | P3 | delete | — | Low |
| Ingress naming: `nginx-ingress*` files deploy the **community** `ingress-nginx` | `apps/platform/nginx-ingress.yaml`, `helm-values/minicloud-1/nginx-ingress-values.yaml` | community `ingress-nginx` | F5-style name misleads; a comment cited the F5 `nginx.org/` annotation (no-op here) instead of the community `nginx.ingress.kubernetes.io/` one | P3 | rename `nginx-ingress*` → `ingress-nginx*`; comment corrected | — | Low |
| `environments/overlays` over-abstraction | 4 `.Files.Get` charts for ns/quota | simple env config | more charts than objects | P3 | optional: flatten | — | Low |
| apps created by blind recursion | `root-app` recurse | layered app hierarchy | ordering is annotation-only | P2 | layer the `apps/` tree | — | Medium |

**Severity key:** P0 = threatens cluster/platform reliability (none found) · P1 = significant structural problem · P2 = maintainability/DX · P3 = cleanup/consistency.

---

## 17. Refactoring Roadmap

**Stage 0 — Document & freeze (no moves).** This report + a dependency check: confirm each `manifests/<x>` is referenced by exactly one `apps/*` Application (trace before moving). Snapshot `argocd app list` health as the baseline.

**Stage 1 — Low-risk cleanup (days).** Evict `data-platform/metabase/provision_dashboard.py` → `ktayl-data-platform` (confirm the pipeline Job clones it); delete `services/_template-helm`; standardize the env-in-namespace cases. *Risk: low. Rollback: git revert.*

**Stage 2 — Boundary corrections (the core).** Introduce `is/` and move the clearly-IS `manifests/` dirs (nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden, erpnext, plane, ktayl*) into `is/{workplace,erp,domains}`. **Each move = one PR per app**: `git mv` the dir, update the single `apps/*` Application `path:`, `argocd app diff` must show **no live change** (path-only), merge, verify `Synced/Healthy`. *Risk: medium (path drift); mitigated by one-app-per-PR + diff gate. Rollback: revert the path.*

**Stage 3 — GitOps restructuring.** Reorganize `apps/` to mirror layers (`apps/platform/{foundation,…}`, `apps/is/{…}`); regroup `manifests/` platform dirs under `platform/{foundation,delivery,…}`. Because `root-app` uses `recurse: true`, the *Application files can move freely* without changing what's deployed (only their own `path:` self-references matter). *Risk: medium. Rollback: revert.*

**Stage 4 — Repository split.** **Skip** (not justified today). Re-evaluate only when a distinct team owns platform vs apps.

**Stage 5 — Long-term model.** Encode the target layout as the law for every new component (see §18) + a hook/CI check that rejects a new `manifests/` dir that isn't under a layer.

For each stage: **changes** (above), **risk** (noted), **dependencies** (Stage 2 before 3; Stage 0 before all), **benefit** (deterministic placement, visible boundary, scalable), **rollback** (git revert of path/dir moves — no live cluster change because `recurse:true` + path-only diffs).

---

## 18. Architectural Rules for Future Components

1. **Decide the layer first via the litmus test** (`platform-vs-information-system.md`): *survives-if-no-insurance?* → `platform/<layer>/`; else → `is/<group>/`.
2. **One packaging pattern per type:** custom-built service → GAP **wrapper chart** (`services/<svc>/helm`); third-party app → **vendor chart + `helm-values/`**; raw CR bundle → **`.Files.Get` packaging chart** under its layer. Never invent a 4th.
3. **No application source code in this repo** — ever. Code lives in the product repo; a runtime Job clones it. (Enforce with a hook.)
4. **The `apps/` tree mirrors the layer tree** — an Application file lives in the layer its target belongs to; never a default "platform" dump.
5. **Capability vs use:** a shared tool is defined **once** under `platform/`; its business use/governance lives under `is/` and *references* it — never duplicated.
6. **Env is a values/overlay dimension, not a namespace-name or a copied manifest.**
7. **Policies, observability, storage each have exactly one home** — don't scatter.
8. A new top-level directory requires an ADR. `manifests/` is **frozen** (no new subdirs; new config goes to a layer).

---

## 19. Final Verdict + the 9 questions

**Verdict:** *Mechanically senior, organizationally entropic.* The delivery engine (helm-only, app-of-apps, wrapper-chart golden path, Kargo 2-env, ESO, sync-waves, policies) is production-grade and should be preserved verbatim. The **filesystem does not express the Platform↔IS and layer boundaries that the repo's own rules now mandate** — fix that *inside the monorepo*. Nothing is dangerous (no P0); the work is P1 structural + P2/P3 cleanup.

1. **Is the separation fundamentally sound?** *Mechanically yes; organizationally no.* The model is right; the directory layout hides it behind two flat catch-alls (`manifests/`, `apps/platform/`).
2. **Where do you mix responsibilities most?** **`manifests/`** (every concern, flat) and **`apps/platform/`** (platform infra + shared services + business apps as peers).
3. **Clearly in the wrong place?** The **stray `provision_dashboard.py`** (code in GitOps repo); **BookStack/Adminer/Homer** filed as "platform" apps; **`kargo-retrieva`** among platform infra; **`_template-helm`** dead scaffold.
4. **Looks mixed but should stay together?** The **3 packaging patterns** (raw/wrapper/vendor) — a correct, documented taxonomy. **dev+prod as two Application files.** **`bmad/`+`docs/`+`.claude/` in-repo.** Platform capabilities (Authentik/Vault/CNPG/AI) serving IS — correct, not a leak. Leave all of these.
5. **Over-engineering?** Barely — the repo is **under-structured, not over-structured.** Only mild over-abstraction: `environments/overlays` as 4 charts for tiny ns/quota bundles.
6. **Repo too large in responsibility?** *Slightly.* It's deployment config + planning + docs + evals + **stray code**. Evict the code; keep the rest. Don't split.
7. **One repo or split?** **Keep one.** Multi-repo solves team-ownership you don't have and adds real coordination cost. Reorganize internally.
8. **Canonical architecture?** Layer-first: `bootstrap → clusters → platform/{foundation,delivery,secrets,networking,observability,security,data,ai,shared-services} → is/{workplace,erp,domains,data-products} → environments`, with `apps/` mirroring those layers. (§13)
9. **Rules so it doesn't rot again?** The 8 rules in §18 — anchored on the `platform-vs-information-system.md` litmus, one-packaging-pattern-per-type, no-code-in-repo (hook-enforced), apps-mirror-layers, and **freeze `manifests/`** so new config is forced into a layer.

> This was read-only analysis — **no cluster or Application resources were modified.** When ready, Stage 1 (evict stray code + delete dead scaffold + env-naming) is the safe, high-signal starting point; it can be executed one reviewed PR at a time with an `argocd app diff` gate on each.
