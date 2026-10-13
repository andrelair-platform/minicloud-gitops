# minicloud-gitops — Remediation Plan (✅ COMPLETE 2026-10-13)

> **Source of diagnosis:** `docs/architecture-audit.md` (2026-10-07). **Status:** ✅ **COMPLETE** — all stages 0–7 executed; `manifests/` eliminated; guardrails enforced. Closing log in §17.
> **Nature of the work:** a controlled **taxonomy / path refactor of the repository**. *Not* a Kubernetes
> re-architecture, *not* a GitOps redesign, *not* a namespace migration, *not* an engine change.
>
> **Target outcome:** someone can understand all of minicloud **by inspecting the repository tree alone**,
> while Argo CD stays **`Synced/Healthy` throughout** the entire migration.

---

## 0. Verdict

The platform's *engine* (app-of-apps, Helm-only, Kargo, Vault/ESO, sync-waves, dev/prod separation, the GAP
golden path) is solid (audit 7–9/10). The weakness is purely **how the system is represented in the repo**:
`manifests/` (55 flat subdirs) and `apps/platform/` (66 "not-a-workload" apps) became catch-alls with no
visible Platform↔IS or layer boundary (audit 4/10 on structure & separation-of-concerns).

**This is an execution strategy, not merely a cleanup proposal.** It fixes the main execution-risk issues
*before* anything moves (see §4 Corrections), so the refactor is **architectural refactoring without runtime
refactoring**.

---

## 1. Invariants — do NOT touch during this work

Keep (the audit confirms these are already strong), and explicitly **forbidden to change in this effort**:

- the **monorepo** (do **not** split into multiple repos);
- **Helm-only**; `bootstrap/root-app.yaml`; the **app-of-apps**; both **ApplicationSets**;
- **Kargo**; `values-dev.yaml` / `values-prod.yaml`; `charts/minicloud-app-deployment`; the **3 packaging patterns**;
- **`services/`** (the golden-path home — a *packaging* layer, kept flat);
- **`helm-values/`**; **Vault + ESO**; **sync-waves**; `docs/`/ADRs; `.claude/rules`.

> **Four hard "do-nots" for the whole project:** do **not** split the repo · do **not** redesign GitOps ·
> do **not** rename namespaces · do **not** touch the deployment engine. This stays a controlled
> taxonomy/path refactor.

---

## 2. Canonical architecture model

```text
bootstrap/
clusters/
  minicloud-1/

platform/            # "survives if ktayl stops selling insurance?" = YES
  foundation/
  storage/
  networking/
  secrets/
  delivery/
  security/
  observability/
  data/
  ai/
  shared-services/

is/                  # = NO (business / employee / insurance capability) — mirrors the docs `is/` pillar
  workplace/
  erp/
  insurance/
  itsm/
  data-products/

services/            # packaging of custom-built services (+ /kargo)   — UNCHANGED
apps/                # architectural / taxonomy projection (Argo CD Applications)
  platform/{foundation,storage,networking,secrets,delivery,security,observability,data,ai,shared-services}/
  is/{workplace,erp,insurance,itsm,data-products}/
  previews/
helm-values/         # vendor values   — UNCHANGED
charts/              # reusable charts — UNCHANGED
environments/        # per-env overlays (ns/quota/limitrange) — UNCHANGED
docs/ · scripts/ · .claude/ · ARCHITECTURE.md
```

**Each tree answers a different question — this separation is the point:**

```text
platform/   → What technical capabilities does the platform PROVIDE?
is/         → What capabilities belong to the Information System / business (the CONSUMERS)?
services/   → HOW are custom-built applications packaged?
apps/       → WHERE does Argo CD classify and deploy everything?
```

**The litmus test for every new component** (authority: `.claude/rules/platform-vs-information-system.md`):

> *If the company stopped selling insurance tomorrow, would this component still have a reason to exist?*
> **Yes → `platform/`** (Cilium, Longhorn, Vault, Prometheus, Grafana, Loki, Argo CD, Kargo, cert-manager,
> Authentik, CNPG operator, LiteLLM). **No → `is/`** (Claims, Underwriting, Policy, ERPNext, Nextcloud,
> Matrix, Stalwart, ITSM, business dashboards).

---

## 3. Canonical homes for ambiguous components (deterministic placement, not philosophical perfection)

> **Nuance (hard rule):** do **not** obsess over making every component fit one category perfectly. Several
> components are legitimately defensible in two layers. **Pick one canonical home, document it here, move on.**
> The objective is *deterministic placement*, not philosophical purity.

| Component | Defensible as… | **Canonical home (decided)** |
|---|---|---|
| Harbor | delivery vs shared-services | **`platform/delivery/`** (it's a registry = part of build/release/run) |
| external-snapshotter | foundation vs storage | **`platform/storage/`** (volume snapshots) |
| Polaris | security vs observability | **`platform/security/`** (config/best-practice compliance) |
| backup-dr (Velero, CNPG backups) | storage vs its own | **`platform/storage/`** (data-protection of storage) |
| cnpg-authentik (Authentik's DB) | data vs shared-services | **`platform/shared-services/`** (per-app DBs live WITH their app) |
| langfuse-base | data vs ai | **`platform/ai/`** (it serves the AI platform) |
| CNPG **operator** | data | **`platform/data/`** (per-app CNPG *clusters* stay with their app, not here) |

| kured / system-upgrade / priority / vpa / node-problem-detector / trust-manager / reloader | foundation vs shared-services | **`platform/foundation/`** (cluster-primitive operators: node lifecycle, resource/priority mgmt, PKI-trust distribution, config-reload) |
| nfs-provisioner | storage | **`platform/storage/`** |
| nginx-ingress / cloudflare-tunnel | networking | **`platform/networking/`** |
| kube-prometheus-stack | observability | **`platform/observability/`** |
| chaos-mesh | observability vs security | **`platform/observability/`** (SRE/reliability fault-injection tooling) |
| falco | security | **`platform/security/`** (runtime security) |
| keda / keda-http-addon | delivery vs shared-services | **`platform/shared-services/`** (autoscaling capability apps consume) |
| nats | data vs shared-services | **`platform/shared-services/`** (messaging bus every domain consumes) |
| postgresql-ai | data vs ai | **`platform/data/`** (shared Postgres datastore; being retired) |
| environments.yaml (ApplicationSet generator) | — | **stays at `apps/platform/` top-level** (a generator over `environments/overlays/*`, not a layer component) |

If a future component is genuinely 50/50, add a row here rather than debating it in a PR.

---

## 4. Corrections applied to the first draft (verified against the repo)

| # | Correction | Verified evidence | Impact |
|---|---|---|---|
| **C1 (critical)** | Custom wrapper-chart services **stay in `services/`**; never moved to `is/insurance/`. Their taxonomy is expressed **only** by moving their Argo CD **Application files** to `apps/is/...`. | Kargo ApplicationSet globs **`path: services/*/kargo`** — moving `services/ktayl-claims/` breaks Kargo freight discovery + the golden path. | Protects Kargo + golden path. **Taxonomy ≠ packaging.** |
| **C2** | `helm-values/` and the 42 multi-source vendor apps are **not moved**; only their Application files reorganize inside `apps/`. | 42 apps use `sources:` referencing `helm-values/` as a `$values` source; **no `../` cross-refs**. | Safe as long as `helm-values/` stays put. |
| **C3** | **Namespace/env uniformization is OUT of scope** of this refactor. | A `git mv` is runtime-neutral; a **namespace rename recreates the workload** (downtime + RWO-PVC risk). | Separate, later, stateful migration. New domains adopt the convention; existing ones untouched here. |
| **C4** | Within `platform/`, migrate **by blast radius**, not alphabetically. | Cilium/Vault/cert-manager are cluster-wide; BookStack is not. | Dangerous components last, each alone, after the pattern is proven. |

**Safety fact that de-risks the whole migration:** the two ApplicationSets glob **only** `environments/overlays/*`
and `services/*/kargo` — **neither globs `manifests/`, `apps/`, or `is/`.** Therefore moving manifests dirs and
reorganizing `apps/` **cannot** regenerate or orphan Applications.

---

## 5. The HARD migration invariant (read before every PR)

A migration unit = **two independent, path-only `git mv`s**:
1. config dir: `manifests/<x>` → `platform/<layer>/<x>` **or** `is/<group>/<x>`;
2. Application file: `apps/platform/<x>.yaml` → `apps/{platform/<layer>|is/<group>}/<x>.yaml`, updating **only** `spec.source.path`.

Because root-app uses `recurse:true` and `metadata.name` is unchanged, the Application object is identical and
the rendered output is byte-identical → the Argo diff is empty.

```text
One refactoring PR MUST change paths only.

DO NOT change simultaneously:
  - metadata.name
  - namespace
  - Helm values
  - chart contents
  - Kubernetes resources
  - image versions
  - any configuration

Expected per-PR loop:
  git mv
      ↓
  update spec.source.path
      ↓
  argocd app diff <app>
      ↓
  EMPTY
      ↓
  merge (squash)
      ↓
  Synced + Healthy
```

**If the Argo diff is NOT empty → STOP that component and investigate.** This gives the strong safety property:
*architectural refactoring without runtime refactoring.*

---

## 6. Execution stages

Every PR follows the §5 loop. Rollback = revert the PR (safe: no live diff). Baseline oracle: `argocd app list`
all `Synced/Healthy` before and after each PR.

### Stage 0 — Freeze + baseline (no moves) — risk: none
- Add `ARCHITECTURE.md` (the §2 tree + per-dir contract + litmus + the §3 ambiguous-home table).
- Declare `manifests/` and `apps/platform/` **FROZEN** (no new entries).
- Capture baseline `argocd app list`.
- Pre-flight already verified: ApplicationSets don't glob moved paths ✅; no `../` cross-refs ✅.

### Stage 1 — Evict clear violations — risk: low
- **Move `data-platform/metabase/provision_dashboard.py` → `ktayl-data-platform` repo** (confirm it exists there, then delete from gitops; `manifests/data-platform/04-pipeline.yaml` already clones that repo → runtime unaffected).
- Delete `services/_template-helm` (dead scaffold; confirm unreferenced).
- Note (don't fix yet) the misfiled Application files (`kargo-retrieva`, `bookstack`, `adminer`, `homer`) — re-homed in Stage 3/4.

### Stage 2 — Create the boundaries — risk: low
- Create `platform/<layers>`, `is/<groups>`, `apps/platform/<layers>`, `apps/is/<groups>`.
- From here, **every new component uses the new layout**; `manifests/` is legacy/read-only.

### Stage 3 — Migrate the IS layer first (lowest blast radius) — risk: low→medium
Order: **BookStack (PILOT)** → rest of `workplace` → `erp` → `itsm` → `insurance`.
- **Vendor/raw IS apps** (nextcloud, stalwart, matrix, jitsi, docuseal, n8n, bookstack, searxng, vaultwarden, erpnext, glpi): move `manifests/<x> → is/<group>/<x>` **and** `apps/workloads/<x>.yaml → apps/is/<group>/<x>.yaml`. One PR each.
- **Custom insurance services** (ktayl-claims/underwriting/policy-service/iam/itsm, ktayl-core): **leave `services/<svc>/` untouched**; move **only** `apps/workloads/ktayl-*-{dev,prod}.yaml → apps/is/insurance|itsm/`.

### Stage 4 — Migrate the platform layer by blast radius — risk: medium, rising
Order: `shared-services → ai → observability → delivery → security → secrets → networking → storage → **foundation LAST**`.
- Path-only move per component. For the 42 multi-source vendor apps, move only the Application file.
- **Cilium, cert-manager, Vault, CNPG operator = last, each in its own PR, at a quiet time, with an extra `argocd app diff` confirmation** (cluster-wide blast radius).

### Stage 5 — Finish `apps/` as the taxonomy projection — risk: low
`apps/is/insurance/ktayl-claims-prod.yaml` must be self-describing. (Largely done incrementally in 3–4.)

### Stage 6 — Guardrails (do NOT skip — prevents re-rot) — risk: none
- **Agent layer:** extend `.claude/hooks/guard-write.py` to block a new `manifests/<dir>` and block app source code (`*.py/*.go/*.ts`) outside `scripts/`/`evals/`/`.claude/`.
- **Human layer:** CI (GitHub Action) failing a PR that (a) adds a top-level `manifests/*` dir, (b) adds an `apps/*.yaml` not under `apps/platform/*` or `apps/is/*`, (c) adds a new top-level dir without an ADR, (d) adds application source code.
- `ARCHITECTURE.md` references `.claude/rules/platform-vs-information-system.md` as the decision authority.

### Stage 7 — Delete `manifests/` when empty — risk: none

---

## 7. Canonical execution sequence (do exactly this order)

```text
1.  Freeze manifests/ and the old catch-all structure
2.  Add ARCHITECTURE.md + capture an Argo CD health baseline
3.  Remove obvious violations: stray Python code, dead scaffold
4.  Create platform/, is/, and the mirrored apps/ hierarchy
5.  Pilot the migration with BookStack
6.  Migrate the rest of the IS layer, one application at a time
7.  Migrate the platform layer from lowest to highest blast radius
8.  Finish reorganizing apps/
9.  Add CI/hooks enforcing the architecture
10. Delete manifests/ only when it is completely empty
```

---

## 8. Per-PR runbook

```bash
# 1. branch
git checkout -b refactor/move-<component>

# 2. path-only moves (example: BookStack, a vendor/raw IS app)
git mv manifests/bookstack            is/workplace/bookstack
git mv apps/platform/bookstack.yaml   apps/is/workplace/bookstack.yaml
#    edit apps/is/workplace/bookstack.yaml: spec.source.path: is/workplace/bookstack   (ONLY this line)

# 3. prove no live change BEFORE merge
ssh controller "argocd app diff bookstack --loglevel warn"   # MUST be empty

# 4. merge (squash) → CODEOWNERS gate on apps/ ; then verify
ssh controller "argocd app get bookstack -o wide | grep -E 'Sync|Health'"   # Synced/Healthy

# rollback if needed: git revert the PR (no live diff to undo)
```

For **custom services** the only move is the Application file (chart stays in `services/`):
```bash
git mv apps/workloads/ktayl-claims-prod.yaml apps/is/insurance/ktayl-claims-prod.yaml
#    (spec.source.path still points at services/ktayl-claims/helm — DO NOT change it)
```

---

## 9. Deferred / out-of-scope (justified)
- **Namespace/env uniformization** (C3) — separate stateful migration, later.
- **`environments/overlays` simplification** (P3), **policy consolidation** (P3), **rename `nginx-ingress*`→`ingress-nginx*`** (P3) — cosmetic, opportunistic.
- **Repo split** — not now.

---

## 10. Priorities

| Priority | Work | Stage |
|---|---|---|
| 🔴 P1 | Evict application code from the GitOps repo | 1 |
| 🔴 P1 | Introduce `platform/` vs `is/` | 2 |
| 🔴 P1 | Decompose `manifests/` | 3–4 |
| 🔴 P1 | Replace `apps/platform`/`workloads` with a real classification | 3–5 |
| 🟠 P2 | Make the Argo CD hierarchy explicit (`apps/` projection) | 5 |
| 🟠 P2 | Group storage (longhorn + snapshotter + backup-dr) | 4 |
| 🟠 P2 | Namespace/env uniformization | *deferred (C3)* |
| 🟢 P3 | Consolidate policies · simplify `environments/overlays` · rename `nginx-ingress*` · delete dead scaffolds | 1 / opportunistic |

---

## 11. Done criteria
- A newcomer understands minicloud from the tree alone: `platform/` = capabilities, `is/` = the insurance
  business, `services/` = custom packaging, `apps/` = the deploy projection.
- `argocd app list` is **all `Synced/Healthy`** throughout — never regressed.
- Guardrails (Stage 6) make the old flat entropy **structurally impossible** to reintroduce.

---

## 12. Recommended first action
**Stage 0 + Stage 1** (write `ARCHITECTURE.md`, freeze, evict `provision_dashboard.py`, delete the dead
scaffold) — all low/zero risk — then the **BookStack pilot** (Stage 3) to prove the path-only / no-live-diff
loop before anything else moves.

---

## 13. Execution log (as executed)

**Session 2026-10-07 — Stages 0, 1, 3 (IS complete) + Stage 4 lot 1. All PRs verified: moved apps
`Synced/Healthy` at new paths, no NEW regression vs the baseline oracle.**

| PR | Scope |
|---|---|
| #1700 | Stage 0 (`ARCHITECTURE.md` + freeze + baseline) + Stage 1 (evict `data-platform/` code, `services/_template-helm`) |
| #1701 | Stage 3 pilot — BookStack → `is/workplace/` (proved the path-only / no-live-diff loop) |
| #1702 | Stage 3 — workplace + erp (10 apps: nextcloud(+mail), stalwart, matrix, jitsi, docuseal, n8n, searxng, vaultwarden, erpnext) |
| #1703 | **bug-fix** — deduplicate + rehome `ktayl-base` (was defined in both apps/platform + apps/workloads) |
| #1704 | Stage 3 — insurance/itsm/iam (custom-service Application files → `apps/is/*`; `services/` unchanged; ktayl-core raw → `is/insurance/`) |
| #1705 | rescue `plane` → `is/workplace/` + ARCHITECTURE refinements (new layers automation/messaging/autoscaling/_demos) |
| #1706 | **Stage 4 lot 1** — platform shared-services + observability (11 apps: adminer, homer, ghproj-exporter, authentik(+ldap-outpost), cnpg-authentik, loki, otelcol, tempo, cert-observability, monitoring) |

IS pillar fully migrated (`is/` + `apps/is/`); `manifests/` 55 → ~30 subdirs. Custom services stayed in
`services/` (golden path + Kargo intact). `data-platform/metabase/provision_dashboard.py` evicted (lives in
`ktayl-data-platform`). **Baseline non-regression oracle** = the 2026-10-07 pre-existing unhealthy set in
`ARCHITECTURE.md`; the rule is "do not ADD to it".

## 14. Stage 4 — refined blast-radius lots

Validated execution order for the rest of `platform/`. **Each cluster-critical component = its own PR,
path-only, empty Argo diff, Synced/Healthy + cluster check, then the next.**

```
LOT A (low)      ✅ DONE : ai · _demos                                       (#1708, #1709)
LOT B (low/med)  ✅ DONE : automation(temporal) · data(non-crit) · harbor · kargo (#1710, #1711)
LOT C (med/high) ✅ DONE : network-policies · rbac · quotas · polaris · external-dns (#1712, #1713)
LOT D (very high)✅ DONE : ESO · Gatekeeper · Vault · Argo CD (1 PR each)     (#1714,#1715,#1716,#1717)
LOT E (foundation):
       Op1 ✅ DONE : relocate the Application FILES → apps/platform/{foundation,storage,data}/
                     (source.path UNCHANGED → byte-identical Application → empty diff)   (#1772)
       Op2 ✅ DONE : manifests/<x> content move + source.path repoint
                     low-risk 8 dirs (#1780) · Cilium (#1781) · Longhorn (#1782) — each byte-identical,
                     verified live Synced/Healthy at new path with ZERO reconcile (cilium pods +
                     longhorn 67/67 volumes unchanged across the merge). manifests/ now ELIMINATED.
```

**Session 2026-10-11 — storage incident RESOLVED; LOT E gate LIFTED; LOT E split Op1/Op2.**
The 2026-10-07 Longhorn degradation was fully resolved this session (67/67 volumes healthy, 0 faulted) —
root cause was a 3-layer stack (WO:RW engine bug → over-provisioning → rebuildRetryCount exhaustion),
fixed by the **Longhorn 1.12.1→1.13.0 chart bump** (#1769) + settings (over-provisioning 200,
auto-engine-upgrade 3; #1770) + deleting retry-exhausted replicas. See
`[[reference_longhorn_stuck_rebuild_113_resolution]]` and `docs/storage-hardening/phase1-execution-plan.md`.

Because the fix was a **Longhorn version upgrade hours old**, LOT E is executed in two phases:
- **Op1 (safe, done this session, #1772):** relocate the LOT E Application *files* into their taxonomy
  homes — `foundation/` (cilium, cert-manager, cert-manager-config), `storage/` (longhorn,
  external-snapshotter, backup-dr, velero), `data/` (cloudnative-pg). **`spec.source.path` is left
  pointing at the existing `manifests/<x>`** → the Application object is byte-identical → **no
  re-render, no resync** of any foundation/storage resource. This completes the Stage-5 apps/ taxonomy
  projection for these components with zero cluster-wide risk.
- **Op2 (deferred, 24–48h storage soak):** the dangerous half — move `manifests/<x>` → `platform/<layer>/<x>`
  and repoint `spec.source.path` for Cilium/Longhorn/cert-manager/CNPG-operator, **one PR each, at a quiet
  time, with an `argocd app diff` confirming EMPTY before merge** (§5 invariant). Only after Op2 repoints
  every component may Stage 7 delete `manifests/`. **⚠️ `manifests/` MUST NOT be deleted until Op2 repoints
  these source.paths** — the relocated Application files still point there.

> §3 placement rows added this session: **cilium/cert-manager → `platform/foundation/`** (CNI + PKI =
> cluster primitives), **longhorn/external-snapshotter/backup-dr/velero → `platform/storage/`**,
> **cloudnative-pg (CNPG operator) → `platform/data/`** (per §3 table; per-app CNPG *clusters* stay with
> their app).

**Session 2026-10-07 (continuation) — LOT A–D complete.** All path-only, byte-identical renders
(rename-purity proven per PR: moved manifests = 0 content change, only the `spec.source.path` lines
edited), each verified live `Synced/Healthy` at its new path with **zero NEW regression** vs the baseline
oracle. CODEOWNERS prod-gate path-refs realigned atomically in C1 (quotas/network-policies/rbac +
retroactive kargo). LOT D verified the `minicloud-platform` AppProject stayed **in place** (original
creationTimestamp preserved → never deleted) and every ExternalSecret stayed `SecretSynced`.
**`manifests/` now holds only the foundation/storage residue** (cilium, longhorn, cert-manager-config,
backup-dr, external-snapshotter, kured, vpa, priority, system-upgrade, cloudflare-tunnel) = LOT E.

**LOT E gate — LIFTED (2026-10-13), see §17.** It had been gated on the 2026-10-07 stale-`tgtd`
incident (belief: only a node reboot clears it). That proved **wrong**: the wedge is remotely
recoverable (cordon the stale nodes + drop the stuck engine CR + move the pod to a clean node — the
frontend wedge doesn't follow the volume). Storage was restored to **67/67 healthy** entirely remotely,
and Cilium/Longhorn were then migrated byte-identically with zero reconcile. No node reboot was needed.

**Nuances (hard):**
- **Vault is ONLY in LOT D** (never migrated early in a "secrets" batch).
- **Argo CD itself** is not a banal `delivery` component — treat it with foundation discipline (isolated PR, check the root app before/after).
- **Gatekeeper** — a policy mistake can block workload create/update cluster-wide → do NOT put all of `security/` in one batch; isolate Gatekeeper.
- **external-dns** — handle carefully but it is lower risk than Cilium/Longhorn (a DNS break ≠ dataplane destruction).
- **Longhorn migration MUST NOT START** until the storage layer is confirmed stable (see the 2026-10-07
  matrix-synapse Longhorn attach incident — a separate storage issue, unrelated to this path refactor).
- **backstage / minicloud-agent / minicloud-crew-agent / platform-demo / retrieva** — classify each
  **individually** (an experiment/demo is not automatically a platform capability); retrieva is the cert
  product (own repo/docs), not `platform/` nor `is/`.

## 15. Remaining stages
- **Stage 5** — ✅ **DONE (2026-10-12)** — `apps/` fully mirrors the layers. Platform side done #1773;
  this session relocated the final 12 `apps/workloads/*` custom-service Application files to their taxonomy
  homes (all `R100` pure renames, `source.path` UNCHANGED → empty Argo diff): longhorn-base→`storage/`,
  platform-demo(+dev)→`_demos/`, backstage→`shared-services/`, agent/crew(+dev)→`ai/`,
  plane(+prod)→`is/workplace/`, retrieva(dev+prod)→new `apps/retrieva/` group (cert product, §14).
  `apps/workloads/` is now **empty/retired**.
- **Stage 6** — ✅ **DONE (2026-10-12)** — guardrails on two layers: `guard-write.py` rules 5–6 (block a new
  `manifests/<subdir>` + app source code outside `scripts/`/`evals/`/`.claude/`/`.github/`, creation-only) +
  the CI check `.github/workflows/architecture-guard.yml` (fails a PR ADDING a new `manifests/*` dir, an
  `apps/*` outside `apps/platform/<layer>/`|`apps/is/<group>/`, a new top-level dir without an ADR, or app
  source code). Both inspect only *new* entries → legacy residue grandfathered. Hook + CI unit-tested.
- **Stage 7** — ✅ **DONE (2026-10-13)** — `manifests/` is **eliminated** (git stops tracking the dir once
  its last contents — cilium + longhorn — moved to `platform/`; 0 tracked files, 0 `path: manifests/` refs).

## ✅ REMEDIATION COMPLETE (2026-10-13)
All stages (0–7) are done. The repo now answers "what is this platform?" from the tree alone:
`platform/<layer>` = capabilities · `is/<group>` = the insurance business · `services/` = custom
packaging · `apps/{platform,is,retrieva,previews}/` = the Argo CD taxonomy projection. `manifests/` is
gone. Guardrails (hook + `architecture-guard` CI) make the old flat entropy structurally impossible to
re-introduce. `argocd app list` stayed within the baseline oracle throughout (no NEW regression).

## 16. Execution log — session 2026-10-12

**Storage soak gate RE-CHECKED and FAILING** — Longhorn at session start: **65 healthy / 1 degraded
(`underwriting-postgres-1`) / 1 faulted (`claims-debezium`, detaching)**, not the 67/67 the LOT E soak
requires. Argo baseline = 9/114 not-`Synced/Healthy`, all within the pre-existing oracle (Kargo-pending
OutOfSync + Progressing on debezium/nextcloud/chaos). **Therefore the dangerous LOT E Op2 content moves
(Cilium, Longhorn → `platform/foundation|storage/`) REMAIN DEFERRED** — the gate is not just un-elapsed,
it has regressed; do not migrate storage/CNI while a volume is faulted.

**Done this session (storage-independent, zero/low cluster risk):**
- **Stage 6 guardrails** — pure repo change, no cluster touch; hook + CI logic unit-tested green.
- **Stage 5** — relocated the 12 `apps/workloads/*` files to taxonomy homes (all `R100` pure renames,
  `source.path` unchanged → empty Argo diff by construction); retrieva → new `apps/retrieva/` group
  (owner decision, §14); `apps/workloads/` now empty. README/gitops.md/ARCHITECTURE updated + the guard
  allow-list extended for `apps/retrieva/`. **Per-PR verification: on merge, confirm each moved app stays
  `Synced/Healthy` and the Argo diff was empty (root-app `recurse:true` → folder is pure taxonomy).**

**(All items that were "still remaining" here were completed 2026-10-13 — see §17.)**

> **Incident note (separate from the refactor):** 2026-10-07 `matrix-synapse` hit a Longhorn
> `FailedAttachVolume` (engine stopped, volume stuck `attaching`, attached nowhere — **not** a stale
> attachment, so no force-detach). Root cause is a Longhorn engine/attach flake, independent of the
> path-only move (which cannot restart a pod). Remediated by deleting the stuck `ContainerCreating` pod
> to trigger a clean re-attach. Treat Longhorn stability as a precondition for LOT E.

## 17. Execution log — session 2026-10-13 (LOT E finished → remediation COMPLETE)

**LOT E Op2 completed; `manifests/` eliminated; Stage 7 done.**
- **Low-risk 8 dirs → `platform/`** (#1780): kured/vpa/priority/system-upgrade/cert-manager-config →
  `foundation/`, backup-dr/external-snapshotter → `storage/`, cloudflare-tunnel → `networking/`. Also
  extended `validate-manifests.yml` to glob `platform/**` + `is/**` (migrated raw CRs were escaping
  kubeconform) and repointed the stale `manifests/kargo` → `platform/delivery/kargo` render target.
- **Cilium → `platform/foundation/cilium`** (#1781) and **Longhorn → `platform/storage/longhorn`** (#1782):
  each byte-identical (`R100` + one `source.path` line), merged one at a time with live verification —
  **cilium pods kept identical ages/restart-counts, longhorn stayed 67/67 volumes healthy across the
  merge → zero reconcile.** `manifests/` then vanished (0 tracked files) = **Stage 7 automatic**.

**Storage incident fully resolved REMOTELY (no power cycle) — corrects the "needs a node reboot" belief.**
The chronic flapping (1–16 degraded, oscillating) was: (a) two `want=1` dev volumes (retrieva-redis,
langfuse-clickhouse) wedged `faulted`/`detaching` on a stale-`tgtd` node — recovered by **cordon both
stale nodes + delete the stuck engine CR + move the pod to a clean node** (the frontend wedge is
target-side, doesn't follow the volume); (b) underwriting-postgres stuck on a failed engine live-upgrade
(1.12.1→1.13.0) + a 3rd replica that couldn't rebuild because the old ThinkPads hit a **fork/PID limit**
(`fork/exec: resource temporarily unavailable`) — cleared the engine by restarting its (replica) pod,
then set that volume to **2 replicas** (sound: CNPG 2/2 instances + 2 Longhorn replicas) → **67/67
healthy, recovery-check STATUS: HEALTHY**. Playbook corrected in
`[[feedback_longhorn_stale_iscsi_target_wedges_engine]]`.

**Durable follow-up (NOT part of this refactor — tracked separately):** the root cause of the storage
flapping is **node fork/PID exhaustion on the overloaded old nodes** (fast-skunk ~53 pods, loving-gannet
~79, fast-heron IM ~1000 threads). Fix = rebalance workloads off the weak ThinkPads (+ optionally raise
`kernel.pid_max`/`threads-max` + kubelet pod-pids). A reboot does **not** fix it (same load reloads).

**Done criteria (§11) — all met:** tree is self-describing; `argocd app list` never regressed past the
baseline oracle; guardrails prevent re-rot; `manifests/` deleted. **This plan is closed.**
