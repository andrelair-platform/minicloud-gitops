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

## 3. LOT 1 — raise the per-pod PID limit (PRIMARY, do first; low-risk)

> **STATUS 2026-10-13/14 — Phase 1 APPLIED & VALIDATED; Phase 2 (durability) + loving-gannet = owner follow-up.**
> - **Live raise DONE** on all reachable IM pod-slices (`pids.max 1024 → 32768`, zero disruption): fast-heron,
>   fast-skunk (was at **1000/1024**), star-kitten (**940/1024**), swift-mac. set-hog (k3s **server**) was
>   already `pids.max=max` (unlimited) — only **agent** nodes carry the 1024 cap.
> - **VALIDATED:** reverting underwriting-postgres to 3 replicas → the 3rd replica **rebuilt successfully on
>   fast-skunk** (the node that previously fork-failed) → volume `healthy`, 3 replicas. Fix proven end-to-end.
> - **⚠️ The live raise is EPHEMERAL** — a per-pod cgroup write reverts when the IM pod is recreated or the
>   node reboots. **Durability needs Phase 2 (§3b): the kubelet `pod-max-pids` config, applied + validated
>   per node.** Until then the 1024 default returns on any IM-pod/node restart.
> - **loving-gannet** could not be reached from this session (no SSH alias / different user+key) → its live
>   raise **and** Phase 2 must be done with owner node access. It wasn't fork-failing (it's the healthy node),
>   so not urgent — but it has the most replicas (52), so it WILL hit 1024 eventually.

### 3a. ✅ DIAGNOSIS CONFIRMED (2026-10-13) — it's the per-pod `pids.max = 1024`
Read live on fast-heron's engine instance-manager (`instance-manager-a6f4…`, pod uid `48e3d3a1…`, Burstable):
```
kubepods-burstable-pod48e3….slice/pids.max         current=992   max=1024    ← BINDING LIMIT
  └─ cri-containerd-….scope/pids.max                current=991   max=18558
kubepods.slice/pids.max  (node top level)           current=1879  max=123725
```
The **pod-level cgroup caps total PIDs at 1024**, and the engine IM already runs **~992 threads** on a
replica-dense node → only ~32 PIDs of headroom. Forking a new engine/replica process — and a live engine
upgrade briefly runs **both** old+new engines → doubles threads — exceeds 1024 → `fork/exec: resource
temporarily unavailable`. **Everything else ruled out:** `kernel.pid_max=4194304`,
`kernel.threads-max≈123729` with only **~3000** threads in use, `ulimit -u=unlimited`, node `kubepods.slice`
pids.max `123725`. This also explains why the underwriting-postgres engine restarted fine on loving-gannet
(its IM was under 1024 then) — it's **not** a global node limit, it's the **1024 per-pod cap** biting
whichever IM accumulates ~1000 threads. So the fix is unambiguous (§3b); the kernel-ceiling tuning is
**NOT needed** and is dropped.

Re-read the limit any time:
```bash
ssh <node> 'for f in $(find /sys/fs/cgroup/kubepods.slice -name pids.max 2>/dev/null); do
  c=$(cat "${f%max}current" 2>/dev/null); m=$(cat "$f"); [ "$m" != max ] && [ "${c:-0}" -gt 300 ] && echo "$c/$m  $f"; done'
```

### 3b. Durability — persist `pod-max-pids=32768` in the kubelet config (OWNER follow-up)
Only the **agent** nodes need it (set-hog/server is already unlimited). Cleanest is the k3s config file
(no unit edit). On each agent node (`fast-heron, fast-skunk, star-kitten, swift-mac, loving-gannet`):
```bash
# append (create if absent) — do NOT clobber existing keys:
sudo sh -c 'grep -q "^kubelet-arg:" /etc/rancher/k3s/config.yaml 2>/dev/null \
  || echo "kubelet-arg:" >> /etc/rancher/k3s/config.yaml
  echo "  - pod-max-pids=32768" >> /etc/rancher/k3s/config.yaml'
sudo systemctl restart k3s-agent      # agents; one node at a time
```
**⚠️ Two hard cautions — this is why it was left as an owner step, not auto-applied:**
1. **A malformed `config.yaml` makes k3s FAIL to start on the next restart/reboot** (latent node outage).
   Validate immediately after the restart: node returns `Ready`, then `sudo systemctl status k3s-agent`.
   Do it in a window where a failed restart can be caught — **one node at a time**, verify before the next.
2. **A k3s-agent restart on a storage node can briefly bounce its Longhorn IM** → that node's volumes
   detach/reattach (the churn we fought). Expect brief per-node rebuild activity; keep
   `concurrent-replica-rebuild-per-node-limit=2`; proceed only while storage is green (67/67).

After each node: confirm `/etc/rancher/k3s/config.yaml` is valid YAML and a *new* pod's slice shows
`pids.max=32768`. The live raise (§3-status) holds the limit until each node is done, so there's no rush.

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
1. LOT 1 diagnose (§3a)            ← ✅ DONE: per-pod pids.max=1024 (IM at 992) is the ceiling
2. LOT 1 live-raise 1024→32768     ← ✅ DONE (5 reachable nodes, zero disruption); loving-gannet = owner
3. LOT 1 verify + revert to 3 repl ← ✅ DONE: 3rd replica rebuilt on fast-skunk → underwriting healthy
4. LOT 1 §3b PERSIST (config.yaml) ← ⏳ OWNER: durable across reboot/IM-restart; validate per node
5. LOT 2a protect set-hog          ← drain its replicas, shed pods
6. LOT 2b/2c swift-mac in, rebalance replicas (quiet window)
7. LOT 2d prune star-kitten AI density
8. LOT 3 ongoing hygiene
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
