# Node Capacity & Fork-Limit Rebalancing Plan (draft)

> **Driver:** the durable follow-up from the 2026-10-13 storage session (`remediation-plan.md` §17).
> Longhorn volumes chronically failed to rebuild / finish engine upgrades on the old nodes with
> `fork/exec … : resource temporarily unavailable` — the node couldn't spawn another process. This is a
> **process/thread (PID) limit**, not CPU/mem exhaustion. This plan fixes the root and rebalances load so
> it can't recur. **Scope: node capacity + scheduling — NOT a GitOps/taxonomy change** (that refactor is
> complete).
>
> Related: `[[feedback_longhorn_stale_iscsi_target_wedges_engine]]`, `[[reference_longhorn_stuck_rebuild_113_resolution]]`,
> `.claude/rules/scheduling.md` (no node-pin SPOFs), `docs/storage-hardening/`.

## 1. The evidence (verified live, 2026-10-13)

| Node | HW | CPU use | Mem use | Running pods | Longhorn replicas | Notes |
|---|---|---|---|---|---|---|
| **set-hog** | 8c/16Gi | **93%** | **80%** | 60 | 11 | **control-plane — dangerously hot**; should be light |
| fast-skunk | 8c/16Gi | 9% | 51% | 53 | 35 | fork-fails despite idle CPU → **PID/thread limit** |
| fast-heron | 8c/16Gi | 29% | 60% | 42 | 24 | fork-fails; stale-`tgtd` node |
| star-kitten | 8c/16Gi | 12% | 57% | **93** | 35 | AI node — most pods; stale-`tgtd` node |
| loving-gannet | 8c/16Gi | 33% | 44% | 48 | **52** | T490 (newest) — most replicas, healthy |
| **swift-mac** | **4c/8Gi** | 75% | 66% | 37 | **0** | 2012 MacBook — weakest HW; **468 GB free disk, 0 replicas** |

**The decisive fact:** the nodes where `fork` fails (fast-skunk 9% CPU, fast-heron 29%) have abundant
CPU/mem. So the failure is a **limit on number of processes/threads**, not resource starvation — the
instance-manager pod hosting ~35 replicas runs ~1000+ threads, and spawning one more engine/replica
process trips a PID ceiling. A reboot does **not** fix this (the same workload reloads and re-hits the
ceiling) — which is why the 2026-10-13 recovery routed *around* the limit rather than rebooting.

## 2. Two independent problems → two independent fixes
1. **Fork/PID ceiling** (why rebuilds/upgrades fail) → **raise the PID limits** (§3, LOT 1). This is the
   high-leverage root fix; the nodes have CPU/mem to spare.
2. **Load concentration** (why it's fragile + set-hog is at 93%) → **rebalance** (§4, LOT 2). Resilience /
   defence-in-depth so one weak node can't wedge the storage layer again.

## 3. LOT 1 — raise the PID/thread ceiling (PRIMARY, do first; low-risk)

### 3a. Diagnose WHICH ceiling is hit (don't blindly raise everything)
Run on the controller; `<IM>` = the instance-manager pod on a fork-failing node (e.g. fast-skunk):
```bash
# (a) the IM pod's cgroup pids controller — the most likely culprit
IM=$(kubectl get pod -n longhorn-system -o wide --field-selector spec.nodeName=fast-skunk \
      -l longhorn.io/component=instance-manager -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n longhorn-system "$IM" -- sh -c 'cat /sys/fs/cgroup/pids.current /sys/fs/cgroup/pids.max 2>/dev/null \
  || cat /sys/fs/cgroup/pids/pids.current /sys/fs/cgroup/pids/pids.max'
# (b) kubelet per-pod pids cap (needs node shell; k3s)
ssh <node> "sudo grep -i podPidsLimit /etc/rancher/k3s/kubelet.config 2>/dev/null; \
            sudo cat /var/lib/kubelet/config.yaml 2>/dev/null | grep -i pid"
# (c) kernel ceilings (world-readable; no sudo)
ssh <node> "cat /proc/sys/kernel/pid_max /proc/sys/kernel/threads-max; awk -F/ '{print \$2}' /proc/loadavg"
# (d) the process RLIMIT_NPROC the engine runs under
kubectl exec -n longhorn-system "$IM" -- sh -c 'ulimit -u'
```
Interpretation: if **pids.max** on the IM pod is a finite number near **pids.current** → it's the
**cgroup pids limit** (fix 3b). If `kernel.threads-max` is being approached (tasks ≈ threads-max) → fix
3c. `pid_max` on modern Ubuntu is usually already 4194304 (not the cause).

### 3b. Fix — raise the kubelet per-pod PID limit (k3s)
The instance-manager legitimately needs thousands of threads on a replica-dense node. Raise the per-pod
cap (default is often a low distro value or inherited):
```bash
# On EACH node, add to the k3s kubelet args (persisted), then restart k3s on that node:
#   agent nodes:        /etc/systemd/system/k3s-agent.service.env  (or the install flags)
#   server (set-hog):   /etc/systemd/system/k3s.service
# add kubelet arg:  --kubelet-arg=pod-max-pids=32768     (from the default; 32768 gives ample headroom)
ssh <node> "sudo systemctl restart k3s-agent"   # or k3s on the server; ONE node at a time, verify Ready
```
Apply **one node at a time**, verify the node returns `Ready` and its volumes re-attach before the next.
Do fast-skunk + fast-heron first (the proven offenders), then the other replica-dense nodes
(loving-gannet, star-kitten).

### 3c. Fix — raise kernel thread/PID ceilings (only if 3a shows these are the limit)
```bash
# persist via sysctl.d (survives reboot), apply live:
ssh <node> "echo 'kernel.pid_max=4194304'   | sudo tee /etc/sysctl.d/99-longhorn-pids.conf
            echo 'kernel.threads-max=512000' | sudo tee -a /etc/sysctl.d/99-longhorn-pids.conf
            sudo sysctl --system"
```
(threads-max scales with RAM; 512000 is safe on the 16 GiB nodes. On swift-mac/8 GiB keep it lower,
~256000, and prefer *reducing* its load — §4.)

### 3d. Verify
Re-run the stuck rebuild/upgrade that failed (or simply observe): on a limit-raised node the
instance-manager can spawn new engine/replica processes → degraded volumes finish rebuilding, and
underwriting-postgres can be returned to **3 replicas** (revert the interim `numberOfReplicas: 2`).

## 4. LOT 2 — rebalance load (RESILIENCE; after LOT 1)

### 4a. Protect the control-plane (highest priority in this lot)
**set-hog is at 93% CPU / 80% mem with 60 pods + 11 Longhorn replicas** — a control-plane node this hot
risks the API server / kine (etcd) for the whole cluster.
- **Move its 11 Longhorn replicas off** — set Longhorn `allowScheduling=false` on set-hog (it should not
  be a storage replica host), then let existing replicas drain/rebuild elsewhere over time (or evict
  gently). `kubectl patch nodes.longhorn.io set-hog -n longhorn-system --type merge -p '{"spec":{"allowScheduling":false}}'`
- **Shed non-control-plane pods** — identify workloads scheduled on set-hog that don't need to be there
  (`kubectl get pods -A --field-selector spec.nodeName=set-hog`) and let them reschedule (remove any
  pin; ensure a `NoSchedule`-free but *preferred-away* posture). Consider a **light taint** +
  tolerations only for genuinely control-plane-adjacent pods.
- Target: set-hog < ~60% CPU, replica count → 0.

### 4b. Use swift-mac's idle storage, cap its compute
swift-mac has **468 GB free and 0 replicas** but is the **weakest compute** (4c/8Gi, 75% CPU, 37 pods).
- **Let it host Longhorn replicas** (it currently hosts none) — replicas are I/O-bound, light CPU → this
  relieves the replica-dense nodes (loving-gannet 52, fast-skunk/star-kitten 35). Confirm
  `allowScheduling=true` + the disk is schedulable (it is).
- **Reduce its pod count** — 37 pods on a 2012/4-core box is a lot; move compute-heavy pods off (prefer
  the 8-core nodes). Keep swift-mac for storage + light services.

### 4c. Even out the replica distribution
Current spread (loving-gannet 52 · fast-skunk 35 · star-kitten 35 · fast-heron 24 · set-hog 11 · swift-mac 0)
is lopsided. After 4a/4b, Longhorn's `replica-auto-balance` (currently `least-effort`) can be nudged to
**`best-effort`** temporarily to let it spread toward swift-mac and off set-hog, then returned to
`least-effort`. Watch rebuild churn; do it when the cluster is quiet.

### 4d. Review star-kitten pod density
star-kitten carries **93 pods** (AI node). If many are idle/experimental, prune or scale-to-zero (several
AI services already use KEDA scale-to-zero). Fewer resident pods = fewer resident processes = more fork
headroom on a stale-`tgtd` node.

## 5. LOT 3 — scheduling hygiene (ongoing, cheap)
- **Node-pin audit** (`scheduling.md`): the only real hostname `nodeSelector` pin found is
  `collab/jitsi-jvb → star-kitten` (legitimate — hostNetwork media). Everything else flagged was
  **pod-anti-affinity `topologyKey: hostname`** = healthy *spread*, not a SPOF. Keep it that way; don't
  add hostname pins (the Gatekeeper `k8snohostnamepin` dryrun policy backstops this).
- Prefer `topologySpreadConstraints` / pod anti-affinity (already the norm) so load self-distributes.
- Keep the control-plane (`set-hog`) light by policy, not by luck.

## 6. Order of execution (safest → highest-value)
```
1. LOT 1 diagnose (§3a)            ← read-only, do now
2. LOT 1 raise pod-max-pids (§3b)  ← one node at a time, verify Ready + volumes; fast-skunk + fast-heron first
3. LOT 1 verify (§3d) + revert underwriting-postgres to 3 replicas
4. LOT 2a protect set-hog          ← drain its replicas, shed pods
5. LOT 2b/2c swift-mac in, rebalance replicas (quiet window)
6. LOT 2d prune star-kitten AI density
7. LOT 3 ongoing hygiene
```

## 7. Risks & rollback
- **k3s restart per node (3b):** brief — that node's pods/volumes re-attach. One node at a time; the rest
  of the cluster is unaffected. Rollback = remove the kubelet arg + restart.
- **Draining set-hog replicas (4a):** triggers rebuilds (I/O churn) — do when storage is green (67/67) and
  quiet; cap concurrency (`concurrent-replica-rebuild-per-node-limit` already 2).
- **auto-balance best-effort (4c):** can cause rebuild churn — temporary, revert to `least-effort` after.
- **Do NOT reboot the old nodes as the fix** — it doesn't address the PID ceiling and fast-heron has hung
  unrecoverably on remote reboot before (`[[feedback_longhorn_stale_iscsi_target_wedges_engine]]`).

## 8. Done criteria
- fast-skunk/fast-heron can spawn new engine/replica processes (no `fork … resource temporarily
  unavailable`); a forced rebuild completes.
- underwriting-postgres back to **3 replicas**, healthy.
- set-hog < ~60% CPU, 0 Longhorn replicas.
- swift-mac hosting a share of replicas; no node > ~40 pods of avoidable load.
- Longhorn stays 67/67 healthy across a full day without manual intervention (the real test that the
  chronic flapping is gone).
