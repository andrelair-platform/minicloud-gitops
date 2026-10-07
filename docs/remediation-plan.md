# minicloud-gitops — Remediation Plan (execution-ready)

> **Source of diagnosis:** `docs/architecture-audit.md` (2026-10-07). **Status:** validated & consolidated — ready for execution.
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
