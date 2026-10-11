# Storage Hardening — Phase-1 Execution Plan (break the post-incident rebuild churn)

> **Status:** proposed — execute in a planned low-load window, NOT live-reactively.
> **Scope:** resolve the specific post-incident Longhorn state (a *churn equilibrium*, not an outage),
> then lock in the Phase-A discipline items from `implementation-backlog.md` so it can't recur.
> **Companions:** `evidence-matrix.md`, `adr-0001-storage-resilience.md`, `implementation-backlog.md`,
> `reliability-validation-plan.md`, `runbooks.md` (RB-2/RB-5/RB-6), memory `[[feedback_longhorn_stale_rofs_after_churn]]`.

## 1. The situation this plan fixes (observed 2026-10-11, post node-reboot cascade)

A **churn equilibrium**, confirmed by live evidence — **not** a data-loss event and **not** a simple slow drain:

| Signal | Observation | Meaning |
|---|---|---|
| `faulted` volumes | **0, throughout** | no data loss; every volume has ≥1 healthy copy |
| `degraded` | **flat ~37** over >1h, oscillating 32↔38 | heals and re-degrades at equal rates → net-zero |
| rebuild events | `Rebuilt` 478 **and** `FailedRebuilding` 108 | rebuilds both succeed *and* fail continuously |
| stopped replicas | **30 on fast-skunk** (of ~38) | stale copies from the incident; need full rebuild |
| failing-rebuild target | `i/o timeout` to star-kitten (`10.42.3.141`), ×5/window | rebuild SYNC times out under contention |
| IM pods | **0 restarts**, mem 0.2–1.2 GiB (headroom) | NOT an OOM / crashing component |
| nodes | CPU ~10–15%, mem 21–70% | NOT CPU/mem starved |
| replica distribution | **loving-gannet ~48**, fast-skunk 30-stopped | heavy **concentration** → single overloaded rebuild *source* |

**Root cause (evidence-backed):** rebuild **sync** throughput on aging consumer SSDs can't keep up when
(a) many stale replicas must be *full*-rebuilt at once and (b) the healthy copies are **concentrated** on
one node (`loving-gannet`), making it the overloaded source → sync RPCs time out → rebuilds fail → retry →
equilibrium. It is a **congestion/contention** problem, not a config bug: the rebuild-concurrency knob is
already at its tuned sweet spot (`2`; `1` deadlocks, `5` thrashes — `manifests/longhorn/01-settings.yaml`),
auto-balance is a no-op on this topology, and the Harbor-flapping symptom rides the same I/O load (its
liveness probe is hardcoded in the goharbor chart → not tunable).

**Why live poking failed (do not repeat):** deleting stuck replicas, excluding/re-including star-kitten,
and uncordoning loving-gannet (the last was a correct stale-cordon fix) did **not** break the equilibrium —
because the limiter is *aggregate sync I/O under contention*, which per-replica surgery doesn't relieve and
every churn-adding action risks re-triggering the RB-2 cascade.

## 2. Strategy — give the rebuild I/O headroom, then de-concentrate (in a planned window)

The rebuilds *do* succeed when they aren't contending. So the plan is **reduce competing load so sync
completes, let it converge to RF=3, then de-concentrate the replicas so a single node is never the
sole source again** — all in an announced low-load window, with data-safety gates and a rollback.

### Pre-flight gates (ALL must hold before starting — abort otherwise)
- **G1 Data safe:** RB-5 shows **0 faulted / 0 volumes at zero usable replicas**. (If any volume is at
  1 usable copy, note it — it's the durability stake this plan protects, not a blocker.)
- **G2 Nodes healthy:** all 6 `Ready`; the 4 storage nodes `allowScheduling=true` except the by-design
  excludes (set-hog control-plane, swift-mac weak-MacBook); **loving-gannet uncordoned**.
- **G3 Baseline captured:** `kubectl -n longhorn-system get volumes,replicas,engines.longhorn.io -o yaml`
  + `settings.longhorn.io` + per-node replica counts, archived to the incident folder.
- **G4 Window announced:** this competes for I/O with running workloads; pick a low-traffic window.

### Step 1 — Quiesce competing I/O (the headroom that lets sync finish)
The rebuild times out because it contends for disk/network with live workloads + CI pushes + backups.
Temporarily remove the avoidable competitors (reversible, no data impact):
1. **Pause the heaviest avoidable writers** to the storage nodes for the window — the simulator/eval
   CronJobs, `db-backup`/`longhorn-backup`/`offsite-restore-verify` CronJobs (`kubectl -n <ns> patch
   cronjob <x> -p '{"spec":{"suspend":true}}'`), and hold CI image pushes (don't merge PRs that trigger
   a `build-and-push`). **Record each so it's un-suspended at the end.**
2. Leave business/prod workloads running (dev-first discipline) — the goal is to shed *batch* I/O, not
   take an outage.
**Gate:** confirm aggregate node disk I/O drops (Grafana) before Step 2.

### Step 2 — Let it converge with the tuned knob (watch, don't poke — RB-2)
With competitors paused, the existing 2-per-node rebuilds should now complete without timing out.
- **Do nothing but watch** for 20–30 min: `degraded` should **trend down monotonically** (not oscillate),
  `FailedRebuilding` events should fall toward zero, `Rebuilt` should dominate.
- **Success:** `degraded → 0`, `0 faulted`, no oscillation for 10 min → go to Step 4 (de-concentrate).
- **If it still times out / oscillates** (contention wasn't the whole story) → Step 3.
- **Stop condition:** any volume hits **0 usable replicas** → STOP, restore from backup (RB-5), abort plan.

### Step 3 — If still contending: one controlled, reversible lever at a time (choose ONE, verify, revert if no gain)
Only if Step 2 doesn't converge. Apply **one**, observe 15 min, revert if it doesn't help — never stack blindly.
- **3a (preferred): clear the stale fast-skunk stopped replicas in small batches** so Longhorn rebuilds
  fresh onto the least-loaded node. Delete **≤3 at a time**, each verified to have a healthy sibling
  elsewhere (RB-5 safety), then wait for those to reach `running` before the next batch. (Doing all 30 at
  once *is* the churn — batch it.)
- **3b: temporarily drop rebuild concurrency to 1** *with* a babysitter: at `1`, a single stuck rebuild
  deadlocks the node's slot (documented) → you MUST watch and hand-delete a stuck target replica to free
  it. Only worthwhile if Step-2 timeouts are clearly aggregate-contention; revert to `2` after convergence.
  This is a `manifests/longhorn/01-settings.yaml` change → **PR, not a live edit** (ArgoCD-managed).
- **Do NOT** reboot a node, bulk-delete pods, restart a healthy IM, or raise concurrency to 5 (RB anti-patterns).

### Step 4 — De-concentrate so a single node is never the sole source again
Once `degraded = 0`, rebalance the heavy nodes (loving-gannet ~48, then fast-skunk) **gently**, at rest:
- Prefer **targeted manual relocation** of the worst hotspots (the method the `01-settings.yaml` comment
  records as what actually worked before), a few replicas at a time, verifying each reaches `running`.
- Do **not** re-enable `replica-auto-balance` as the mechanism — it's a no-op/thrash on this topology
  (evidence E-rebalance). Manual, observed relocation only.
- **Target:** no storage node holds >~30% of total replicas; every RF=3 volume spread across 3 distinct
  active nodes.

### Step 5 — Restore normal operation + lock in the discipline
1. **Un-suspend** everything paused in Step 1 (CronJobs, resume CI). Confirm backups run green again.
2. If 3b was used, **PR the concurrency back to `2`**.
3. Verify end state (Section 3).
4. **Lock in Phase-A backlog items** so this can't recur (from `implementation-backlog.md`):
   - **RB-6 staggered re-admission** is the standing rule after ANY node reboot (a freshly-empty node is
     a scheduler magnet → the concentration that caused this).
   - **No bulk node reboots** for a Longhorn wedge (the trigger of this whole incident) — `runbooks.md`.
   - Add a **replica-concentration alert** (PrometheusRule): warn when any node holds >40% of replicas, so
     the imbalance is caught before the next incident, not during it.
   - Add a **`degraded`-volume-duration alert**: warn if any volume stays `degraded` > 2h (catches a churn
     equilibrium automatically instead of via a human eyeballing the recovery-check).

## 3. Success criteria (define "done")
- `faulted = 0` **and** `degraded = 0`, stable for ≥15 min (no oscillation).
- No storage node holds a disproportionate replica share (>~30%).
- `recovery-check`: Longhorn ✓, ArgoCD degraded set clears, Harbor stops flapping (no new core/registry
  restarts for 30 min — it rides the same I/O relief).
- All Step-1 suspensions reverted; backups green; concurrency back to `2`.
- A short result card appended here (what converged it: Step 2 alone, or which Step-3 lever).

## 4. Rollback / abort
- Every step is reversible: un-suspend CronJobs, revert the concurrency PR, stop deleting replicas.
- **Hard abort** (RB-5): if any volume reaches **0 usable replicas**, STOP all action and restore that
  volume from its Longhorn/Velero backup before doing anything else. Data safety outranks convergence.

## 5. What this does NOT do (deliberate scope)
- It does **not** change the hardware reality (consumer SSDs, 4 active nodes). The durable fix for
  *recurrence* is the Phase-B/C backlog (replica-placement policy, possibly a dedicated storage node /
  faster disk) — tracked in `implementation-backlog.md`, validated per `reliability-validation-plan.md`.
- It does **not** touch prod data paths beyond shedding batch I/O; prod stays up throughout.

> **One-line summary for the owner:** the cluster is *safe* (0 faulted) but stuck in a rebuild churn
> because aging disks can't sync many concentrated-source rebuilds at once under load. The fix is a
> planned, low-load window: shed batch I/O → let it converge → de-concentrate → re-enable, with a
> data-safety abort gate — executed deliberately, never as live reactive poking.

---

## Resolution — as executed (2026-10-11)

The Phase-1 operational levers above (shed I/O, watch at concurrency 2, batch-clear, concurrency→1,
detach/reattach) **did NOT converge it** — proving the churn was not I/O contention. Escalation to the
deferred **Longhorn version upgrade (LOT E)** was the actual fix, and the root cause turned out to be
**three stacked problems**, each hidden behind the previous:

1. **Engine `WO:RW` rebuild bug (Longhorn 1.12.1).** Rebuilds copied to ~99% then failed at the final
   write-only→read-write promotion (`replica is not in mode WO: RW`, `cannot set rebuilding=true from
   state rebuilding`). Upstream [#13914](https://github.com/longhorn/longhorn/issues/13914) +
   [#13992](https://github.com/longhorn/longhorn/issues/13992). **Fix: upgrade chart 1.12.1 → 1.13.0**
   (PR #1769) + enable `concurrent-automatic-engine-upgrade-per-node-limit` so HEALTHY volumes migrate
   to the v1.13.0 engine. This alone healed ~14 (degraded 30→16).

2. **Replica over-concentration → disk unschedulable.** `loving-gannet` (the node that survived the
   reboot cascade) accumulated ~47 replicas and crossed the `storage-over-provisioning-percentage: 100`
   cap (`ScheduledTotal 355.9G > ProvisionedLimit 351.7G`) → its disk went `Schedulable=False` → the
   remaining rebuilds had nowhere to place (`rebuilds=0`), despite ~47% real free space. **Fix: raise
   over-provisioning 100 → 200** (PR #1770) → disk schedulable again.

3. **`rebuildRetryCount` exhaustion.** The 14 stuck replicas had `rebuildRetryCount=5` (maxed) +
   `healthyAt=''` — they'd burned their retries during the 1.12.1 WO:RW churn, so Longhorn had **given
   up** initiating their rebuilds. **Fix: delete the retry-exhausted `stopped` replicas** (fail=0, with
   a healthy running sibling) → Longhorn created fresh replicas (retry reset) → which, on the v1.13.0
   engine with placement restored, **finalized**.

**Outcome:** all three together drained it to **67/67 healthy, 0 faulted** (0 data lost at any point).
The chart bump is merged (#1769); the two settings are persisted to gitops (#1770).

### Lessons
- The "shed-I/O-and-wait" Phase-1 plan was the wrong model: this was **stacked engine/scheduling/retry
  bugs**, not I/O contention. The **version upgrade was the real fix** — justified only once the WO:RW
  root cause was confirmed against the release notes.
- **Verify convergence before declaring stuck.** The rebuilds finalized on a *delay* after the fixes;
  an interim "stuck" call was premature — always re-check the live count before concluding.
- A degraded volume **won't** auto-migrate its engine (Longhorn defers engine upgrade until healthy) —
  the chicken-and-egg that required the detach/retry-reset path for the degraded set specifically.
- **Prevention (Phase-A backlog):** the replica-concentration alert (>40%/node) would have caught
  loving-gannet before it crossed the over-provisioning cap; RB-6 staggered re-admission prevents the
  concentration in the first place.
