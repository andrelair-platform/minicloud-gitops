# Storage Incident Runbooks (Longhorn on the ThinkPad cluster)

> Derived from the 2026-10-08/09 incident. The golden rule, learned the hard way:
> **a Longhorn attach problem is almost never fixed by rebooting a node or bulk-deleting pods — those are
> what turn a one-volume wedge into a cluster-wide congestion cascade.** Use the least-invasive action.

## RB-0 — Decision tree (start here)
```
Volume(s) not attaching?
├─ ONE volume, pods elsewhere healthy? ........... RB-1 (cordon-and-move the single pod)
├─ MANY volumes cycling attaching/faulted? ....... RB-2 (congestion cascade — do NOT bulk-delete)
├─ A node pings but sshd dead / NotReady? ........ RB-3 (hung node)
└─ Engine 'exit 2' + tgtadm target errors? ....... RB-4 (stale iSCSI target)
Always first: is any volume truly data-at-risk (0 surviving replicas)? → RB-5 before anything.
```

## RB-1 — Single volume stuck attaching (the common case)
**Cause:** the pod landed on a node that can't attach this volume (stale target, or transient).
**Do:**
1. Find the volume's healthy replica node: `kubectl -n longhorn-system get replicas.longhorn.io -l longhornvolume=<pv> -o custom-columns=NODE:.spec.nodeID,STATE:.status.currentState,FAILED:.spec.failedAt`
2. `kubectl cordon <the-node-the-pod-is-stuck-on>`
3. `kubectl -n <ns> delete pod <the-stuck-pod>` → it reschedules onto a clean node → attaches.
4. Once `Running`+volume `attached/healthy`: `kubectl uncordon <node>`.
**Do NOT:** reboot the node; delete many pods; restart instance-managers.
**Evidence it works:** E15 (matrix/criticals recovered this way).

## RB-2 — Many volumes cycling (congestion cascade)
**Recognise:** `UNKNOWN`/`FAULTED` counts oscillating in lockstep; dozens of not-ready pods piled on ONE node;
possibly `pthread_create: Resource temporarily unavailable` in longhorn-manager logs.
**Root behaviour:** too many simultaneous engine-starts/attaches on one node (thundering herd). This is NOT a
static limit (see ADR/evidence E6).
**Do:**
1. **Stop adding churn.** Do NOT bulk-delete pods — it re-clusters the herd (E14).
2. Identify the magnet node (most not-ready pods): `kubectl get pods -A --field-selector status.phase=Pending -o wide | awk '{print $8}' | sort | uniq -c | sort -rn`
3. **Cordon the magnet node** so no more pile on; then **let Longhorn's retry backoff drain it** — a few
   attaches complete per cycle as capacity frees. Watch, don't poke.
4. If a specific critical volume must come up now, use RB-1 on **that one** only.
5. Re-admit any cordoned node only once the cluster is **at rest** (see RB-6 staggered re-admission).
**Do NOT:** reboot nodes; mass-delete; raise "IM limits" (there are none — E6).

## RB-3 — Node hung after reboot (pings, sshd dead, NotReady)
**Reality today:** these ThinkPads have **no working out-of-band power** (power off/reset need sshd — E19;
WoL only powers *on*). A hung node currently needs a **physical** power-cycle.
**Do:**
1. Confirm it's hung pre-sshd: `ping <ip>` works, `ssh <node> uptime` refused, node `NotReady` for >5 min.
2. Confirm the cluster is safe without it: other nodes Ready, no volume at 0 replicas (RB-5).
3. **Do not reboot more nodes.** A physical power-cycle of the hung node is the only in-band-safe recovery.
4. After it returns: verify `iscsiadm -m session | wc -l` is sane; **keep it cordoned**; re-admit per RB-6.
**Prevention:** Phase-C boot-resilience (C1) + out-of-band power (C2, if battery allows).

## RB-4 — Stale iSCSI target wedge (engine `exit 2` in startFrontend)
**Recognise:** engine log `tgtadm … delete … logicalunit … can't find the logical unit` / `unbind … tid N …
does not exist`; volume `faulted` while a replica is `healthy`/`failedAt` empty.
**Do:** this is per-node — use **RB-1 (cordon-and-move)** to get the volume onto a clean node. The stale
target on the bad node clears on its next clean detach or a node reboot (last resort, RB-3 caveats apply).
**Do NOT** assume the whole cluster is wedged — it's the one node's tgtd.

## RB-5 — Data-at-risk check (run FIRST in any storage incident)
```
kubectl -n longhorn-system get volumes.longhorn.io -o json | python3 -c '
import sys,json; d=json.load(sys.stdin)
for v in d["items"]:
  s=v.get("status",{})
  if s.get("robustness")=="faulted":
    print(v["metadata"]["name"], "state="+str(s.get("state")))'
```
For each faulted volume, check it still has a usable replica (`failedAt` empty) **or** an app-level copy
(CNPG/ensemble). If a volume has **no** surviving copy → **STOP all remediation, restore from backup**
(Velero/CNPG/Longhorn backup) before touching anything. Throughout this incident data loss stayed 0 (E18).

## RB-6 — Staggered node re-admission (after reboot/replacement)
A freshly-empty node is a **scheduler magnet** (E13). To avoid re-triggering RB-2:
1. Node returns → **leave it cordoned**.
2. Wait until the cluster is **at rest**: `kubectl get pods -A | grep -vE 'Running|Completed'` is ~empty and
   Longhorn robustness is steady (no mass `attaching`).
3. `kubectl uncordon <node>` **without** simultaneously deleting/rolling other pods.
4. Watch for ~10 min: if a herd forms (RB-2 signature), re-cordon and investigate.

## RB-7 — Read-only diagnostic toolkit (safe; used in the investigation)
- Robustness snapshot: `kubectl -n longhorn-system get volumes.longhorn.io -o json | …Counter(robustness)`
- Per-node replica load: aggregate `replicas.longhorn.io .spec.nodeID`
- IM limits (confirm no ceiling): `crictl inspect <im> | …resources.pids/memory`, `exec cat /proc/self/limits`
- pthread/resource errors: `kubectl -n longhorn-system logs -l app=longhorn-manager --since=Nm | grep pthread_create`
- iSCSI stale check: per node `sudo iscsiadm -m session | wc -l` vs that node's attached-volume count
- Which fragility class: CNPG PVCs carry label `cnpg.io/cluster`; everything else stuck = raw-RWO.

## What NOT to do (the anti-patterns this incident proved)
- ❌ Reboot a node to clear a Longhorn wedge (triggers mass reschedule → herd).
- ❌ Bulk-delete pods to "spread" them (re-clusters the herd onto the next empty node).
- ❌ Uncordon a freshly-rebooted node while reschedules are in flight (magnet).
- ❌ "Raise the instance-manager pids/thread limit" (there is no limit set — E6; it's a null change).
- ❌ Restart instance-managers to fix an attach (disrupts their healthy volumes for no proven benefit).
