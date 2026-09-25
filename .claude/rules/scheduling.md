# Scheduling & placement — no node-pin SPOFs

**Never hard-pin a workload to a specific node.** No `nodeSelector: {kubernetes.io/hostname: <node>}`
and no *required* `nodeAffinity` on `kubernetes.io/hostname` / `metadata.name`. Longhorn volumes are
**network-attached** — a pod runs on any node and attaches its volume over the network — so a hostname
pin buys nothing and turns that node into a **single point of failure**: if it's full, cordoned, or
down, the pod can't schedule and its Service goes to 503 (2026-09-25: grafana pinned to a full
`star-kitten` sat `Pending`/`FailedScheduling` ~38 min; the audit found **20** such pinned workloads,
7 of them nailed to the control-plane node). See [[feedback_node_pin_spof_and_failover]].

## Do this instead
- **Data locality:** set Longhorn **`dataLocality: best-effort`** on the StorageClass/volume — a *soft*
  preference to run near a replica that **fails over freely**. Never a hard pin.
- **Real hardware needs** (GPU, hostNetwork media, node-local disk): pin to a **capability label**
  (`node-role/ai`, `gpu=true`), never a hostname — and opt out of the guard with the workload label
  **`scheduling.minicloud/hostname-pin-allowed: "true"`**.
- **Spread, don't pin:** use `topologySpreadConstraints` / pod anti-affinity to distribute replicas;
  keep the control-plane node (`set-hog`) light.
- **Stateful pod that must move:** `strategy: Recreate` (RWO Longhorn — avoid multi-attach).

## Guardrails (enforced)
- **Gatekeeper `k8snohostnamepin`** (`manifests/gatekeeper-policies/22..23`) denies hostname pins on
  Deploy/STS/DaemonSet/Rollout. It ships in **`enforcementAction: dryrun`** (audit-only) until the 20
  existing pins are remediated, then flips to **`deny`**. The `hostname-pin-allowed` label is the opt-out.
- **Alert `KubePodStuckPending`** (`manifests/monitoring/35-scheduling-alerts.yaml`) fires at 10 min
  (warning) / 30 min (critical) so a scheduling failure surfaces fast, not via a 503.

## Removing an existing pin (the remediation, staged post-convergence)
Remove the `nodeSelector`/affinity in the app's helm-values/manifest, set the StorageClass
`dataLocality: best-effort`, ensure `strategy: Recreate` for RWO stateful pods, PR a few at a time and
verify each reschedules + reattaches. Do it when Longhorn is settled — each removal reschedules that
stateful pod (brief per-app downtime).
