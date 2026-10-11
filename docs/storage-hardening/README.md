# Storage Hardening — investigation, plan & resolution

> **Status: RESOLVED (executed 2026-10-11) — cluster back to 67/67 volumes healthy, 0 faulted.**
> The remediation was executed: root cause was a 3-layer stack (Longhorn 1.12.1 WO:RW engine bug →
> replica over-concentration hitting the over-provisioning cap → `rebuildRetryCount` exhaustion),
> fixed by the **chart upgrade 1.12.1→1.13.0** + settings (over-provisioning 200, auto-engine-upgrade
> 3) + deleting retry-exhausted replicas. **See `phase1-execution-plan.md` §"Resolution — as executed
> (2026-10-11)"** for the full account, plus the follow-on alerting gap-fix
> (`platform/observability/monitoring/21-longhorn-alerts.yaml`: over-provisioning-trap +
> degraded-stuck alerts).
>
> _Historical note:_ this set was originally produced as a **read-only investigation** (no mutations,
> reboots, or setting changes) delivered for review **before** execution, LOT E, and any version
> upgrade. The proposal/ADR/evidence framing below is kept as the decision record (that pre-execution
> snapshot); where the as-executed outcome differs, the resolution section is authoritative.

## Documents in this set
| File | Purpose |
|---|---|
| `evidence-matrix.md` | Every root-cause claim → log evidence + timestamp → confidence (CONFIRMED / SUPPORTED / UNVERIFIED). |
| `adr-0001-storage-resilience.md` | The decision record: alternatives, trade-offs, failure domains, rollback, and what is explicitly **not** proven. |
| `implementation-backlog.md` | Phased, per-change spec (problem / evidence / files / preconditions / procedure / validation / rollback / blast radius). |
| `reliability-validation-plan.md` | Controlled fault-injection scenarios, measurable recovery targets, explicit stop conditions. |
| `runbooks.md` | Operational runbooks (the correct remediation for each failure mode; what NOT to do). |
| `phase1-execution-plan.md` | **The deliberate remediation to execute** (planned low-load window) for the 2026-10-11 post-reboot *churn equilibrium* — shed batch I/O → let it converge → de-concentrate replicas → re-enable, with data-safety abort gates. |

## Headline finding (one paragraph, evidence-backed)
The 2026-10-08/09 incident was **not** caused by a misconfigured resource limit. The instance-managers
have **no** pids/memory/nproc ceiling (`crictl` `pids.limit=none`, `mem.limit=none`; `RLIMIT_NPROC=unlimited`;
`vm.max_map_count=1048576`; node `threads-max` ~124k vs ~1–3.5k used). The incident was a **self-inflicted
congestion cascade**: a legitimate but *wrong-tool* remediation — **physically rebooting nodes** to clear an
iSCSI stale-target wedge — triggered `node-down-pod-deletion-policy=delete-both-…` → a **mass pod
reschedule** → the freshly-rebooted (empty) node became a **scheduler magnet** → a **thundering herd** of
simultaneous engine-starts/volume-attaches → transient `pthread_create: Resource temporarily unavailable`
and attach timeouts → volumes **cycling** `attaching↔faulted`. Bulk pod-deletes then **re-clustered** the
herd. **No data was lost.** All 13 volumes still cycling at investigation time are **raw-RWO singletons**;
**zero of the 11 CNPG-managed volumes** were affected (they failed over at the app layer).

## What this changes about the "obvious" fixes
- **"Raise the instance-manager pids/thread limit" → REFUTED.** There is no limit set; there is nothing to
  raise (`evidence-matrix.md` E1–E5). Proposing it would be turning a wrong hypothesis into an action.
- **"Add a smart plug / fix remote power" → addresses recoverability of a *hung node*, not the attach
  congestion.** Keep it, but do not claim it fixes the storage incident class.
- **"Migrate DBs to CNPG" → supported by recovery evidence, but CNPG still sits on Longhorn PVCs.** Its
  resilience came from *app-level failover*, not from avoiding Longhorn. It reduces blast radius for DBs;
  it does not fix raw-RWO singletons (matrix media, loki, grafana, vault) and must be validated, not assumed.

## The actual highest-value levers (detailed in the ADR/backlog)
1. **Remediation discipline (operational, zero-infra):** never reboot a node or bulk-delete pods to fix a
   Longhorn wedge; use **cordon-and-move of the single affected pod** (confirmed to work this incident).
2. **Congestion controls:** reduce simultaneous attach/rebuild load; stagger node re-admission after a reboot
   so an empty node does not draw the whole herd.
3. **Avoid the trigger:** graceful drain instead of hard reboot; reconsider `node-down-pod-deletion-policy`.
4. **(Secondary, must be validated) ** boot-resilience + out-of-band power; selective CNPG adoption; raw-RWO
   singleton reduction.

Every lever above is a **hypothesis to validate via `reliability-validation-plan.md`**, not a certainty.
