# Storage Hardening — Phased Implementation Backlog (proposal, not executed)

> Priority order = confidence order. **Phase A** is zero-infra/low-risk and does not need validation first.
> **Phases B–D** are **gated on `reliability-validation-plan.md`** — each is a hypothesis, not a proven fix.
> Each item: Problem · Evidence · Files/GitOps · Preconditions/backup · Procedure · Validation/success ·
> Rollback · Risk/blast-radius. **Nothing here is applied yet.**

---
## Phase A — Operational discipline + visibility (do first; no cluster-behaviour change)

### A1. Codify the Longhorn-wedge remediation rule (cordon-and-move, never reboot/bulk-delete)
- **Problem:** the cascade was triggered by node reboots + bulk pod-deletes used as remediation (E12–E14).
- **Evidence:** E15 (cordon-and-move works) vs E12–E14 (reboot/bulk-delete trigger the herd). CONFIRMED.
- **Files/GitOps:** `docs/storage-hardening/runbooks.md` (new, this set) + a new auto-loaded rule
  `.claude/rules/storage-incident-response.md` (or extend `scheduling.md`). Docs only — **no** `apps/`/`manifests/`.
- **Preconditions/backup:** none (docs).
- **Procedure:** land the runbook + rule via PR (CODEOWNERS on `.claude/rules`).
- **Validation/success:** the rule exists + is referenced by `ops-runbooks`; next incident follows it (0 node
  reboots / 0 bulk-deletes for a Longhorn wedge). Measurable: incidents resolved by cordon-and-move only.
- **Rollback:** revert the doc PR.
- **Risk/blast-radius:** none (no cluster change).

### A2. Early Longhorn-degradation alert (surface before it cascades)
- **Problem:** the degraded/faulted churn was discovered via a manual recovery-check, late.
- **Evidence:** incident was already cascading before it surfaced; `recovery_check` flagged it only on a manual run.
- **Files/GitOps:** a new `PrometheusRule` under `manifests/monitoring/` (→ will move to `platform/observability`
  per the refactor). Alert on `longhorn_volume_robustness` ∈ {degraded>N for >M min, faulted>0}, and on
  `count(volume state=attaching) > K for > M min` (herd detector).
- **Preconditions/backup:** confirm the Longhorn Prometheus metrics are scraped (ServiceMonitor exists).
- **Procedure:** add the rule file + an Application (or extend monitoring) via PR; CODEOWNERS.
- **Validation/success:** synthetic — scale a test workload to force a brief degraded state → alert fires
  within M min; faulted→alert. Confirm no false-positive during normal rebuilds (tune N/M/K via V-C data).
- **Rollback:** remove the PrometheusRule (pure additive).
- **Risk/blast-radius:** low (observability only); only risk is alert noise → tuned by V-C thresholds.

### A3. recovery-check CNPG-aware postgres check — ✅ ALREADY DONE (record)
- **Problem:** `PostgreSQL (chat)` false-alarm (checked dead STS pod `postgresql-synapse-0`).
- **Evidence:** synapse DB is CNPG `synapse-postgres`, healthy; recovery-check hardcoded the old name.
- **Files/GitOps:** `minicloud-ops/recovery_check/{checks.py,config.py}` — **committed `d887adc`**, verified OK.
- **Status:** done; listed for completeness. No further action.

---
## Phase B — Congestion controls (config; GATED on validation V-B/V-C)

### B1. Reduce simultaneous rebuild pressure during recovery
- **Problem:** simultaneous mass rebuild+attach = the thundering herd that produced transient pthread EAGAIN (E7/E8/E11).
- **Evidence:** E8/E11 (congestion, not a static limit) + F3 (`concurrent-replica-rebuild-per-node-limit=2`).
- **Files/GitOps:** Longhorn `setting` CR / helm-values for Longhorn (`helm-values/minicloud-1/longhorn-*` or
  the Longhorn Application values). **Record the current value (2) as the rollback baseline.**
- **Preconditions/backup:** capture current settings (`kubectl get settings.longhorn.io -o yaml` snapshot).
- **Procedure:** propose lowering `concurrent-replica-rebuild-per-node-limit` 2→1 **only as a temporary
  recovery posture**, re-raise after. **CAVEAT:** there is **no** Longhorn "concurrent *attach* limit"
  setting (UNVERIFIED that a rebuild-limit alone tames the *attach* herd) → this is exactly what V-C tests.
- **Validation/success:** V-C fault-injection with limit=1 vs 2 → measure peak `attaching` count, time-to-
  converge, and whether `pthread_create` recurs. Success = no cycling >K, converge < target, 0 pthread.
- **Rollback:** restore the recorded value (single field).
- **Risk/blast-radius:** **cluster-wide** Longhorn rebuild pace (all volumes). Wrong value → slower healing;
  reversible. Must be validated before standardising.

### B2. Staggered node re-admission (prevent the empty-node magnet)
- **Problem:** a freshly-rebooted empty node drew 62 pods → herd (E13).
- **Evidence:** E13/E14 CONFIRMED.
- **Files/GitOps:** runbook only (operational) — optionally a short `scripts/` helper in `minicloud-ops`.
- **Preconditions:** none.
- **Procedure:** after any node reboot/replacement, keep it **cordoned**, then uncordon **only when the
  cluster is at rest** (no pending reschedules), optionally admit workloads gradually. Documented in runbooks.
- **Validation/success:** V-B — reboot one node under load, follow the staggered procedure → no herd pile-up
  (max not-ready-on-one-node < threshold), converge < target.
- **Rollback:** n/a (procedure).
- **Risk/blast-radius:** low (reduced-capacity window while cordoned).

### B3. Revisit `node-down-pod-deletion-policy`
- **Problem:** `delete-both-…` (F4) drives the mass reschedule on node loss → the herd.
- **Evidence:** F4 + E12 CONFIRMED.
- **Files/GitOps:** Longhorn setting (helm-values). Record baseline.
- **Preconditions:** understand the trade-off: a less-aggressive policy means stateful pods **don't auto-move**
  on real node loss (manual intervention needed) — this is a **failover-semantics change**, not free.
- **Procedure:** evaluate `do-nothing` vs `delete-deployment-pod` vs current; decide per V-E.
- **Validation/success:** V-E — induce node loss under each policy; measure reschedule herd size vs failover time.
- **Rollback:** restore baseline (single field).
- **Risk/blast-radius:** cluster-wide failover behaviour. Must be validated; default to current until proven.

---
## Phase C — Recoverability (so reboots are rarely needed & never trap us) — GATED on V-D/V-F

### C1. Boot resilience (a reboot must never hang pre-sshd)
- **Problem:** rebooted ThinkPads hung pre-sshd (not recoverable remotely) during the incident.
- **Evidence:** fast-heron hung ~15 min pings-but-no-sshd (captured live 10-09); memory `feedback_efibootmgr_ubuntu_entry`.
- **Files/GitOps:** `minicloud-ansible` (UEFI boot entry / GRUB / fstab `nofail` for non-root mounts).
- **Preconditions:** per-node BIOS/console access (physical) for the boot-order fix.
- **Procedure:** ensure Ubuntu UEFI entry is first + non-root mounts `nofail`; ansible play per node.
- **Validation/success:** V-F — reboot a node, confirm it reaches sshd+Ready < target, never drops to emergency.
- **Rollback:** boot config is per-node; revert via console.
- **Risk/blast-radius:** single node per change.

### C2. Out-of-band power (make a hung node remotely recoverable) — EVALUATE, don't assume
- **Problem:** power off/reset needs sshd (E19); a hung node can't be power-cycled remotely; no IPMI/vPro.
- **Evidence:** E19 CONFIRMED (power-broker source).
- **CRITICAL CAVEAT (do not present as solved):** a **smart plug cannot force-off a laptop running on its
  battery** — cutting mains leaves it on battery. Options: (a) BIOS "disable internal battery"/"on-AC-only"
  per model (loses the UPS effect), or (b) accept the plug only power-*cycles* once the node is already off.
  Feasibility is **per-model UNVERIFIED**.
- **Files/GitOps:** `minicloud-ops/maas-power-broker.py` (off/reset → plug API) + hardware.
- **Preconditions:** confirm each ThinkPad can run AC-only / battery-disable, or accept the limitation.
- **Procedure:** evaluate per model; if viable, wire the plug into the broker's off/reset path.
- **Validation/success:** V-F2 — from a deliberately-hung node, trigger broker `reset` → node power-cycles
  without a site visit. **If battery defeats it → record as NOT viable; rely on C1 + D1 instead.**
- **Rollback:** remove the plug path; broker reverts to ssh.
- **Risk/blast-radius:** single node; a mis-wired plug could cut a healthy node → gate behind confirmation.

---
## Phase D — Blast-radius reduction for critical state (architectural, incremental) — GATED on V-G

### D1. Prefer app-level-replicated (CNPG) for critical DBs currently raw-RWO/STS-singleton
- **Problem:** raw-RWO singletons are the fragile class (E16); some critical DBs are STS singletons
  (e.g. `postgresql-ai-0`, `temporal-postgresql-0`) not CNPG.
- **Evidence:** E16 CONFIRMED (0/11 CNPG cycled; 13/13 raw-RWO cycled). E17 caveat: CNPG still on Longhorn.
- **Files/GitOps:** per-workload (its own repo/manifests) + CNPG cluster CR (ref `docs/cnpg-standard.md`).
- **Preconditions/backup:** **full DB backup + maintenance window** per workload (stateful migration).
- **Procedure:** per the CNPG migration playbook (`reference_cnpg_migration_playbook`): additive CNPG →
  dump/restore parity → host cutover → bake → cleanup.
- **Validation/success:** V-G — induce a node loss hosting the migrated DB's replica → app stays up (failover);
  compare to the raw-RWO baseline.
- **Rollback:** per-workload restore from backup (playbook).
- **Risk/blast-radius:** the migrated workload only; stateful ⇒ backup-gated.

### D2. Reduce single-replica raw-RWO consumers / review RF
- **Problem:** several raw-RWO volumes are RF=1 (data stranded when their one node is down).
- **Evidence:** incident: `retrieva-dev` pg, `claims-postgres-1`, `langfuse-zookeeper` were RF=1 (captured live).
- **Files/GitOps:** per-workload PVC/storageclass + Longhorn volume RF.
- **Preconditions:** capacity for extra replicas (replica imbalance F6 must be considered).
- **Procedure:** raise RF for genuinely-critical raw-RWO volumes; accept RF=1 only where app provides
  redundancy (e.g. a zookeeper ensemble member) — document the choice.
- **Validation/success:** a node loss leaves no critical volume fully unavailable.
- **Rollback:** lower RF back.
- **Risk/blast-radius:** per-volume; extra replicas add rebuild/storage load (ties to B1).
