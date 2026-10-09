# Storage Hardening — Reliability Validation Plan (fault-injection, proposal)

> Purpose: **prove or refute** each proposed lever (D1–D4 / backlog B–D) *before* it is trusted or
> standardised — so we do not repeat turning a hypothesis into a fact. All scenarios run **on `dev`-class
> / non-critical workloads first**, announced, with **explicit stop conditions** and a tested rollback.
> **None of this is executed yet** — it is the gate for any Phase B–D change.

## Ground rules
- **Baseline capture before every run:** `kubectl get volumes.longhorn.io -o yaml`, `settings.longhorn.io`,
  per-node `iscsiadm -m session | wc -l` vs attached count, replica distribution, node mem/threads.
- **One variable per run.** Record start/end timestamps + the full metric series.
- **Data-loss is the hard stop everywhere:** if any volume with no surviving replica/app-copy appears →
  **STOP, do not proceed, restore from backup.**
- **Prefer a dedicated throwaway namespace** (`st-validate`) with synthetic RWO + CNPG workloads that mirror
  the real fragility classes, so production stateful sets are untouched where possible.

## Measurable recovery targets (define "good")
| Metric | Target | Why |
|---|---|---|
| Time-to-converge after a single induced fault | **≤ 10 min** to all-`healthy`/`degraded` (0 `faulted`, 0 cycling) | matches an acceptable homelab RTO |
| Peak concurrent `attaching` volumes on any one node | **≤ 5** | above this, the herd/pthread risk appeared |
| `pthread_create: Resource temporarily unavailable` occurrences | **0** | its presence = congestion regime |
| Max not-ready pods on any single node during recovery | **≤ 10** | the 62-pod pile-up was the magnet signature |
| Data loss | **0 always** | non-negotiable |
| CNPG-backed critical DB downtime on single-node loss | **≈ 0 (failover)** | the resilience claim to confirm |

## Scenarios

### V-A — Reproduce & characterise the pthread/congestion regime (diagnostic, no fix applied)
- **Inject:** on `st-validate`, create N raw-RWO volumes (e.g. 20), then force simultaneous attach (schedule
  all their pods to one node via nodeSelector). Capture per-node mem, thread count, `pthread_create` log, attach times.
- **Goal:** confirm (or refute) that the EAGAIN appears only under simultaneous-attach pressure and identify
  the **actual** limiting resource (open question 1) — watch node `MemAvailable` + `/proc/<engine>/status` threads at the moment of failure.
- **Success/Exit:** we can state the limiting resource with evidence, or confirm it's pure contention.
- **Stop:** any real (non-`st-validate`) volume degrades → abort.

### V-B — Single node reboot WITH staggered re-admission (tests B2/A4)
- **Inject:** gracefully drain → reboot ONE node (a non-critical one); keep it cordoned on return; uncordon
  only at rest; optionally admit gradually.
- **Compare:** vs the incident's reboot-then-immediate-uncordon behaviour.
- **Success:** peak not-ready-on-one-node ≤ 10; converge ≤ 10 min; 0 pthread; 0 data loss.
- **Stop:** herd pile-up > threshold, or a node hangs pre-sshd (→ triggers V-F), or any data loss.

### V-C — Rebuild-concurrency knob (tests B1)
- **Inject:** same induced multi-volume degrade, run once at `concurrent-replica-rebuild-per-node-limit=2`
  (baseline) and once at `=1`; measure converge time, peak attaching, pthread count.
- **Success/decision:** keep the value that minimises cycling without unacceptable rebuild slowdown.
  **If `=1` does NOT reduce the *attach* herd (only rebuilds), record that B1 is insufficient alone.**
- **Stop:** data loss; or convergence worse than baseline on both settings → revert, do not adopt.

### V-D — iSCSI stale-target lifecycle (tests E9/open question 2)
- **Inject:** on a `st-validate` volume, force an **unclean** detach (kill the consumer node's kubelet / hard
  power a node hosting the engine) and observe whether a stale tgtd target remains and wedges the next attach.
- **Goal:** confirm whether the stale target is *created by* an unclean detach (initiating) vs a secondary symptom.
- **Success:** we can state the lifecycle with evidence + confirm cordon-and-move (or a clean detach) clears it.
- **Stop:** any real volume affected.

### V-E — `node-down-pod-deletion-policy` comparison (tests B3)
- **Inject:** simulate node loss (cordon+shutdown a non-critical node) under the current policy vs a candidate.
- **Measure:** reschedule-herd size vs failover time (how long a stateful pod stays down).
- **Decision:** pick the policy with the best herd-vs-failover trade-off; **default to current if inconclusive.**
- **Stop:** a stateful workload becomes unrecoverable, or data loss.

### V-F — Boot resilience + out-of-band power (tests C1/C2)
- **V-F1 (boot):** reboot a node with the C1 boot-resilience change → must reach sshd + `Ready` ≤ target,
  never drop to emergency. 3 consecutive clean reboots to pass.
- **V-F2 (power):** deliberately hang a node (or simulate) → trigger the broker `reset` → confirm it
  power-cycles **without a site visit**. **If the laptop battery defeats the plug → record C2 as NOT viable**
  (honest negative result), rely on C1 + D1.
- **Stop:** a node becomes unrecoverable remotely AND no one can reach it physically → escalate.

### V-G — CNPG vs raw-RWO failover (tests D1/D4)
- **Inject:** node loss hosting (a) a migrated CNPG DB's instance and (b) an equivalent raw-RWO singleton.
- **Measure:** app-downtime + data integrity for each.
- **Success:** CNPG ≈ 0 downtime (failover) & intact; quantifies the blast-radius benefit of D1/D4.
- **Stop:** data loss on the raw-RWO baseline beyond the known RF=1 risk → note, don't proceed to prod migration.

## Reporting
Each scenario produces a short result card (inject · metrics vs targets · pass/fail · evidence links) appended
to this file. A lever (B/C/D) is **adopted only if its scenario passes**; a failed/inconclusive scenario keeps
the lever in "candidate" state and the ADR unchanged.
