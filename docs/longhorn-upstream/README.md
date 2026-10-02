# Longhorn upstream deploy manifests (reference / record — NOT ArgoCD-managed)

These are the **exact upstream `deploy/longhorn.yaml` manifests applied by hand** during the staged
Longhorn climb (see `../reliability-longhorn-upgrade.md`). They are committed **for the record** —
versioned, reviewable, reproducible — to incrementally close *Finding A* (the Longhorn **core** is
installed/upgraded by manual `kubectl apply`, not Helm/ArgoCD/Ansible).

> ⚠️ **These files are deliberately under `docs/` so ArgoCD NEVER syncs them.** They are a *record of what
> was applied*, not a deployment source. Do **not** move them under `manifests/` — the `longhorn-base`
> ArgoCD app (`manifests/longhorn`) would then try to apply the full upstream manifest on top of the
> hand-managed core, duplicating/conflicting with it. `longhorn-base` manages **only** the Longhorn
> *settings / recurring-jobs / pvc-labels*, never the core.

## How the core is actually managed (current state)
- **Install + upgrade mechanism:** `kubectl apply -f longhorn-<version>.yaml` on the controller, one minor
  per hop (Longhorn forbids skipping minors). Prereqs (open-iscsi + multipath blacklist) are the Ansible
  `longhorn-prereq` role; the core itself is **not** in Ansible/Helm/ArgoCD.
- **Per hop:** apply the manifest → wait manager/CSI rollout + `current-longhorn-version` → health-gate to
  0-faulted → `concurrent-automatic-engine-upgrade-per-node-limit=1` to migrate all volume engines live →
  revert to 0 → dwell. Full log: `../reliability-longhorn-upgrade.md` (*Climb log*).

## Applied so far
| Version | Applied | Notes |
|---|---|---|
| v1.7.3 | 2026-10-01 (hop 1) | from v1.6.0 |
| v1.8.2 | 2026-10-01 (hop 2) | |
| v1.9.2 | 2026-10-01 (hop 3) | 1.9 bumps instance-manager image |
| v1.10.2 | 2026-10-01 (hop 4) | |
| v1.11.3 | 2026-10-01 (hop 5) | **floor for multi-source rebuild**; first to officially support k8s 1.36 |
| v1.12.1 | 2026-10-01 (hop 6 — **TARGET**) | **climb complete: 1.6.0 → 1.12.1**; latest stable on k8s 1.36; V2 GA but V1 kept |

## The proper end state (tracked follow-up, post-climb)
Migrate the Longhorn **core** to the official **Helm chart managed by ArgoCD** (upgrade = a `targetRevision`
bump → CODEOWNERS review → ArgoCD applies, reconciled + auditable). Do this as a dedicated change on a
settled cluster — **never mix a management-method migration with a version migration.** Until then, add the
next hop's manifest here when it's applied.
