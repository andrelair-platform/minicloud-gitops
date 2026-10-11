# Storage Incident — Evidence Matrix

> Read-only evidence gathered 2026-10-09 ~12:45–12:49 UTC, plus evidence captured live during the
> 2026-10-08/09 incident. Confidence: **CONFIRMED** (direct observation/command output) ·
> **SUPPORTED** (strong circumstantial, consistent with multiple observations) · **UNVERIFIED**
> (could not obtain direct evidence; stated as open question, not fact).

## Environment facts (CONFIRMED)
| ID | Fact | Evidence (cmd / output) | Timestamp |
|---|---|---|---|
| F1 | Longhorn **v1.12.1** (manager + engine) | `longhorn-manager:v1.12.1`; `default-engine-image=…longhorn-engine:v1.12.1` | 2026-10-09T12:45:42Z |
| F2 | 6 nodes, all `Ready` throughout the post-reboot phase | `kubectl get nodes` (repeated) | 10-09 ~10:5x–12:4x |
| F3 | `concurrent-replica-rebuild-per-node-limit = 2` | `kubectl get settings.longhorn.io …` | 2026-10-09T12:45:42Z |
| F4 | `node-down-pod-deletion-policy = delete-both-statefulset-and-deployment-pod` | same | 2026-10-09T12:45:42Z |
| F5 | `default-replica-count = 3` | same | 2026-10-09T12:45:42Z |
| F6 | Replica distribution **imbalanced**: loving-gannet 49, star-kitten 38, set-hog 28, fast-skunk 23, fast-heron 11 | `kubectl get replicas.longhorn.io` aggregation | 2026-10-09T12:45:42Z |

## Root-cause claims
| ID | Claim | Confidence | Evidence + timestamp | Notes / caveats |
|---|---|---|---|---|
| **E1** | IM container has **no pids limit** | **CONFIRMED** | `crictl inspect` IM on fast-skunk & star-kitten → `pids.limit=none` | 2026-10-09T12:48:49Z |
| **E2** | IM container has **no memory limit** | **CONFIRMED** | `crictl` `mem.limit=none`; pod spec `resources.limits` empty (`requests.cpu=480m` only) | 12:45:42Z / 12:48:49Z |
| **E3** | IM process **RLIMIT_NPROC = unlimited** | **CONFIRMED** | `exec cat /proc/self/limits` → `Max processes unlimited` | 2026-10-09T12:45:42Z |
| **E4** | k3s **podPidsLimit unset → unlimited (-1)** | **CONFIRMED** | no `pod-max-pids` in k3s config on fast-heron/fast-skunk | 2026-10-09T12:45:42Z |
| **E5** | `vm.max_map_count = 1048576` (not limiting) + node `threads-max` ~124k vs **~1–3.5k used** | **CONFIRMED** | per-node `cat /proc/sys/…` + `ps -eL | wc -l` | 2026-10-09T12:48:49Z |
| **E6** | ⇒ The `pthread_create` failure was **NOT a static resource ceiling** | **CONFIRMED (by refutation)** | E1–E5 jointly refute every static limit | This invalidates "raise the IM limit" as a remedy. |
| **E7** | `pthread_create: Resource temporarily unavailable` **did occur** on engine start during the storm | **CONFIRMED** | longhorn-manager log lines captured live | 2026-10-08 ~07:09:5x; recurred during matrix engine starts |
| **E8** | The pthread failures are **transient peak-load contention**, not standing | **SUPPORTED** | `grep -c pthread_create` over last 24h window now = **0** (12:47:18Z) while static limits all clear (E6) → only present under simultaneous load | Exact limiting resource at peak (thread-stack memory vs system thread pressure) is **UNVERIFIED** — historical per-node mem/thread peaks were not captured. |
| **E9** | iSCSI **stale tgtd target** was the **initiating** failure of the *original* matrix wedge | **SUPPORTED** | engine `startFrontend` log: `tgtadm … unbind … tid 3 … this access control rule does not exist` / `delete … logicalunit … can't find the logical unit`; engine `exit status 2` | 2026-10-08 ~19:45–19:52 (captured live) |
| **E10** | Stale iSCSI sessions exist on nodes (sessions > attached volumes) | **SUPPORTED** | earlier: fast-heron 4 sessions / 3 attached (=1 stale), star-kitten 4/2 (=2 stale), swift-mac 4/4 (clean); later per-node session counts 2–12 | counts are time-variant; exact stale deltas not re-measured at 12:4x |
| **E11** | The *later* mass cycling (13 vols) is **congestion**, not per-node stale targets | **SUPPORTED** | volumes faulted on *freshly-rebooted/clean* nodes too (star-kitten, set-hog); `pthread=0` yet still cycling; lockstep flips (`UNKNOWN=17↔FAULTED=17`) | distinguishes the *initiating* wedge (E9, per-node) from the *amplified* cascade (congestion) |
| **E12** | Node reboot → **mass pod reschedule** (via F4 policy) | **CONFIRMED** | F4 policy + observed Pending/ContainerCreating waves after each reboot | |
| **E13** | A **freshly-rebooted empty node is a scheduler magnet** → herd | **CONFIRMED** | `62` not-ready pods piled on fast-heron after uncordon; repeated when re-admitted | 10-09 ~ before each spread |
| **E14** | **Bulk pod-delete re-clusters** the herd onto the next emptiest node | **CONFIRMED** | after deleting fast-heron's pods, `15` not-ready piled on fast-skunk | 10-09 observed |
| **E15** | **cordon-and-move of a single pod** recovers a wedged volume (low collateral) | **CONFIRMED** | matrix recovered on loving-gannet/swift-mac via cordon+move earlier; criticals recovered after the first spread | 10-08/09 |
| **E16** | **CNPG workloads recovered; raw-RWO singletons are the fragile class** | **CONFIRMED** | **13/13 cycling volumes are raw-RWO; 0/11 CNPG** cycling; authentik-cnpg-1 served while cnpg-3 restarted; synapse-postgres-1 healthy throughout | 2026-10-09 ~12:4x |
| **E17** | CNPG resilience is from **app-level failover**, not from avoiding Longhorn | **SUPPORTED** | CNPG PVCs are Longhorn-backed (same storage class); recovery came from operator re-creating/re-attaching instances | ⇒ migrating to CNPG is **not** a proven storage fix; must be validated |
| **E18** | **No data loss** at any point | **CONFIRMED** | `faulted` volumes always retained ≥1 healthy replica or app-level copy; final `FAULTED` counts transient; DBs intact | throughout |
| **E19** | The remediation node reboots were themselves forced by **no out-of-band power** (ssh-dependent) | **CONFIRMED** | `maas-power-broker.py`: `off/reset = ssh sudo poweroff|reboot`; `on = WoL`; `query = ping` → a hung node can't be power-cycled remotely | 10-08 (reviewed source) |

## Explicit open questions (UNVERIFIED — do not state as fact)
1. The exact limiting resource of the `pthread_create` EAGAIN at the storm peak (thread-stack memory vs
   transient system-wide thread spike). Node metrics at peak were not captured. → Validation plan V-A.
2. Whether the initiating iSCSI stale-target (E9) was caused by an *unclean detach during the node reboot*
   or pre-existed. → Validation plan V-D.
3. Whether reducing attach/rebuild concurrency actually prevents the cascade, or merely slows it. → V-C.
4. Whether the replica imbalance (F6/E6) materially worsens herd behavior on specific nodes. → V-B.
