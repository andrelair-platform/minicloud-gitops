# Reliability: Storage Tiering & Failure-Domain-Aware Replication

**Status:** In progress (P0 executing) · **Owner:** Platform · **Started:** 2026-10-01
**Board:** GitOps — Platform Engineering (#3)

> Frozen baseline + live experiment log. Do not rewrite past measurements — append.

## 1. Problem

Node events (power blip, reboot, Longhorn iSCSI wedge) trigger **cluster-wide Longhorn
rebuilds** across slow, CPU-limited consumer laptops. Because *all* state is 3×-replicated
synchronously over the LAN, every event copies GBs 3× through a storage fabric that saturates
almost immediately → **heals take ~a day**, and the churn itself wedges more nodes. This is
inherent to laptop-Longhorn, not a tunable bug. For real users this is unacceptable; the fix is
architectural, not incremental.

## 2. Governing principle (the rule that drives build decisions)

> **Avoid redundant durability layers. Use Longhorn replication primarily when *storage* owns
> durability; use 1 replica when the *application* owns durability — but only after validating
> independent failure-domain placement, quorum behaviour, and recovery.**

Corollary: **replication follows business criticality, not "it has a PVC."**

## 3. Storage tiers (replication follows criticality)

| Tier | StorageClass (target) | Longhorn | App protection required | Examples |
|---|---|---|---|---|
| Ephemeral | `local-ephemeral` / emptyDir | 0 | none | caches, build artifacts, reconstructable queues |
| Rebuildable | `longhorn-rebuildable-1r` | 1r | none | Prometheus, Loki, Tempo, Harbor **dev** registry, qdrant, dev DBs, indexes |
| App-HA | `longhorn-app-ha-1r` | 1r | **mandatory** quorum/replication + independent failure domains | Vault (raft), NATS (JetStream R≥3), ZooKeeper, multi-instance CNPG |
| Standard | `longhorn-standard-2r` | 2r | optional | important single-instance services |
| Critical | `longhorn-critical-3r` | 3r + tested backup | ideally HA | irreplaceable single-instance business state, nextcloud files |

> StorageClass `numberOfReplicas` applies to **new** volumes only; existing volumes are changed
> per-volume (`kubectl patch volumes.longhorn.io … numberOfReplicas`). Reducing replicas is a
> **live** operation (no PVC recreation); only moving *to* local/ephemeral needs recreation.

### 3a. The App-HA 1r rule (hard gate — learned, do not skip)
`1r` preserves resilience **only if** the application's replicas *and* their single Longhorn
replicas sit in **independent failure domains**, verified after the change:
- app pods on distinct nodes (podAntiAffinity / topologySpread),
- each volume's surviving replica on a **distinct, storage-healthy** node (verify the survivor
  node — `best-effort` locality *biases* but does not *guarantee*; `strict-local` guarantees but
  couples the volume to the pod's node),
- quorum/replication-factor of the actual data confirmed (e.g. per-JetStream-stream R-factor,
  not cluster size),
- the target node must have passed storage qualification (never put a single copy on an
  unqualified/flaky node).

## 4. Roadmap (P0–P5)

- **P0 — eliminate unnecessary replicated bytes.** Inventory every PVC → classify → set
  appropriate replication. Batches, one workload-family at a time, verify after each.
- **P1 — observability + node qualification.** disk latency/util/iowait, net retransmits, Longhorn
  replica state, rebuild duration, volume robustness, node pressure, read-only-filesystem events.
  Node **storage qualification** (SMART/NVMe, dmesg, iSCSI) for fast-skunk + swift-mac — **done**
  (both disks SMART-PASSED; instability was iSCSI/churn, not hardware). Gap: SMART only readable via
  the smartctl-exporter pod (CLI absent on nodes); add a `loving-gannet` SSH alias.
- **P1.6 — rebuild-throughput (MOVED UP — the real MTTR lever; see §8).** Measured ~0.9 GiB/min,
  target-disk- and LAN-independent → the bottleneck is the Longhorn V1 rebuild path + source-side
  processing. This gates how fast a failed node recovers, so it outranks cosmetic placement.
- **P2 — storage topology.** Dedicated storage nodes + dedicated disk (OS vs Longhorn) via
  Longhorn node/disk tags. Fix the loving-gannet/swift-mac imbalance (replica-auto-balance
  evaluated here, not in P0 — balancing itself creates traffic). **Large-volume migration is
  throughput-bound (~0.9 GiB/min) → do it as slow background work; prioritise small volumes + P1.6.**
- **P3 — Longhorn modernization (priority raised by P1.6).** Staged supported upgrade from **1.6.0**
  toward the current release (**1.13.0**, 2026-09-29), validating the compat matrix at every hop.
  Not a direct jump. **Benchmark empirically (don't assume linear gains):** `replica-rebuild-concurrent-
  sync-limit` = 1/2/3 (scale/multi-source rebuild, v1.11+) tested on a **disposable 3r volume**
  (remove 1 replica, 2 healthy sources) — NOT a 1r→2r migration; and `fast-replica-rebuild-enabled`
  + snapshot checksums weighed against their CPU/IO cost. (No V1 bandwidth QoS knob — that's V2/SPDK.)
- **P4 — safe auto-remediation.** A `minicloud-reliability-operator`:
  `observe → diagnose → validate (healthy replica + backup RPO + node/disk cond) → remediate →
  verify → escalate`. **Never** blind `kubectl delete`. Builds on `minicloud-ops`/`sdlc_loop`.
- **P5 — chaos / recovery testing.** Deliberately: power off worker, net disconnect, fill disk,
  kill a Longhorn replica, reboot a storage node, kill a CNPG primary, restore a DB from R2.
  Measure MTTD / MTTR / RTO / RPO / rebuild duration / availability.

### Acceptance criteria (targets to validate in P5, not assumptions)
```
stateless / rebuildable workloads   MTTR < 5 min
application-HA workloads             MTTR < 10 min
critical storage rebuild            < 30–60 min
CNPG RPO ≤ 15 min · RTO ≤ 60 min (with scheduled restore tests, not just backups)
```
> "Backup" is not protection until **restore is tested**. Velero restore-drills already exist
> (app/erpnext/ktayl restore-drill, offsite-restore-verify); extend to CNPG + record RTO/RPO.

## 5. Reliability findings

### RF-001 — Stateful rollout → RWO attach outage (2026-10-01)
```
Trigger:   Nextcloud helm change (retire bitnami PG) forced a Deployment rollout
Expected:  routine pod replacement (seconds)
Actual:    ~12–15 min 503 — new pod on fast-skunk; Longhorn engine error; 50Gi vol stuck attaching
Root dep:  RWO Longhorn attach on a transiently-unhealthy node
Data loss: 0        Availability impact: yes
Fix:       cordon fast-skunk → move pod to loving-gannet → clean attach
Lessons:   (1) stateful+RWO on fragile Longhorn IS the heal-time problem (stateless = secs)
           (2) fast-skunk = emerging 2nd weak node (after swift-mac) → P1 qualification
           (3) anticipate rollouts from "config" changes; pre-steer pod placement
```

## 6. P0 execution log + evidence

| Node (Longhorn scheduled) | Baseline | After B1 | After B2 (Vault) |
|---|---:|---:|---:|
| fast-heron | 177 Gi | 167 | 167 |
| fast-skunk | 115 Gi | 115 | 115 |
| loving-gannet | 327 Gi | 317 | 312 |
| set-hog | 265 Gi | 255 | 250 |
| star-kitten | 268 Gi | 268 | 258 |
| swift-mac | 24 Gi | 24 | 24 |
| **Longhorn volumes** | 59 | 58 | 58 |
| **Vault storage copies** (vault-0/1/2) | 9 | 9 | **5** |
| **Vault raft peers** | 3 | 3 | 3 |
| **unhealthy volumes** | 0 | 0 | 0 |
| **data loss** | — | 0 | 0 |

- **Batch 1 (gitops#1515):** retired unused bitnami `nextcloud-postgresql` (migrated to CNPG).
  `postgresql.enabled:false` + `externalDatabase→CNPG` → ArgoCD removed STS; orphaned PVC+PV
  deleted → **~30 Gi reclaimed** (fast-heron/loving-gannet/set-hog −10 each). Triggered RF-001.
- **Batch 2 (Vault), live per-volume patch, one ordinal, gated:**
  - vault-2 → 1r, survivor **set-hog** (pod-local), healthy, raft 3/3 ✅
  - vault-1 → 1r, survivor **loving-gannet** (pod-local), healthy, raft 3/3 ✅
  - vault-0 **held at 3r** — fast-skunk not storage-qualified (deferred risk).
  - Method proven: `best-effort` locality + reduce + **verify survivor node** → deterministic.
  - **~20 Gi reclaimed** (2 members × 2 removed replicas × 5 Gi). Vault copies 9→5.

### Deferred risks / open items
- **vault-0 at 3r** until fast-skunk passes P1 storage qualification (SMART currently unreadable).
- **Node qualification:** fast-skunk (RF-001 engine error) + swift-mac (2012 MacBook, prior outage)
  = two weak nodes → P1.
- **Imbalance** loving-gannet 312 vs swift-mac 24 Gi → P2 (not during P0).
- **Longhorn 1.6.0** → P3 staged upgrade (stuck/limbo-replica states hit this session).
- **Concurrency** `concurrent-replica-rebuild-per-node-limit=2` (gitops#1514): 5 saturates/thrashes,
  1 deadlocks on a stuck rebuild, 2 is the tuned sweet spot.

## 7. Remaining P0 batches (each with the §3a gate, one family at a time)
- **B3 NATS** — classify by **per-JetStream-stream R-factor** (not cluster size): R≥3 → 1r
  candidate; R=1 persistent → keep storage replication or raise stream R. Verify meta-quorum +
  streams fully replicated after each ordinal.
- **B4 ZooKeeper** (quorum) → 1r.
- **B5 Rebuildable** — Prometheus/Loki/Tempo/Harbor-dev/qdrant/dev DBs/caches (biggest byte win).
- **B6 CNPG** — last, per-DB scrutiny; authentik-cnpg (2 instances) evaluated separately
  (streaming repl ≠ 3-member quorum).

**P0 outcome (closed):** total running replicas ~158→130, total replicated state ~1160→984 Gi
(~−15%), 0 data loss, 0 unhealthy. B1 (bitnami retired) + B2 (Vault 9→5) + B3 (NATS **audited→deferred**:
R=1 streams incl. CLAIMS_CDC_PROD → RF-002) + B5.1 caches + B5.2 observability (Prom/Loki→2r, others→1r)
+ B4 ZooKeeper + B5.3 Qdrant + B5.4 dev DBs, all →1r. **Finding:** P0 cut *total* state ~15% but the
worst-case single-node exposure barely moved (301→286 Gi) — it's dominated by *critical* data on an
*overloaded* loving-gannet → **worst-case is a P2 placement problem, not a P0 count problem.**

## 8. P1.6 — rebuild-throughput investigation (the real MTTR lever)

**RF/P1.6 — replica rebuild throughput bottleneck.** Measured on a live rebuild (loving-gannet source
→ star-kitten target, 1 GbE):

| Signal | Value | Reading |
|---|---|---|
| steady rebuild throughput | **~15 MB/s ≈ 0.9 GiB/min** | (earlier 0.45 was ramp-up; steady ~2×) |
| network RX | ~15.7 MB/s | **~13% of 1 GbE** → not network-bound |
| target disk write / iowait | ~13.5 MB/s / **0%** | target disk not the limit |
| SATA (swift-mac) vs NVMe (fast-skunk) | ~equal | **disk type was never the constraint** |

**Leading (observed) constraint:** the Longhorn **V1 rebuild path + source-side** replica/snapshot
processing. (Source-side disk-read / instance-manager CPU / snapshot+checksum profiling still pending —
hence "dominant observed", not "definitive".) Destination network bandwidth + destination SSD + SATA-vs-
NVMe are **ruled out** as the primary constraint.

### The reliability KPI this produced: recovery-pressure
```
recovery_pressure ≈ worst-case exposure ÷ rebuild throughput     (multiplicative levers)
  today:                286 Gi ÷ 0.9 GiB/min ≈ 5.3 h   (revised down from a ~9.5 h over-estimate)
  after P2 (→145 Gi):   145 ÷ 0.9           ≈ 2.7 h
  after P2 + upgrade:   145 ÷ 2.0           ≈ 73 min
```
P2 shrinks the numerator; P1.6/upgrade grows the denominator. Both are needed; neither alone suffices.

### P1.6 next controls (empirical)
1. **Longhorn 1.6→1.13 staged upgrade** (priority raised — biggest denominator lever).
2. Benchmark **scale rebuild** `replica-rebuild-concurrent-sync-limit`=1/2/3 on a **disposable 3r volume**
   (remove 1 replica, 2 healthy sources) — the node-loss-recovery case; NOT a 1r→2r migration.
3. Benchmark **fast rebuild** (`fast-replica-rebuild-enabled` + snapshot checksums) vs its CPU/IO cost.
4. Profile the **source** during a rebuild (disk read MB/s, IM CPU, snapshot layout) to confirm the hypothesis.
5. Continue P2 (reduce exposure) — a lighter source *also* rebuilds faster.

## 9. P2 log
- **P2.1 (ClickHouse 30 Gi relocate off loving-gannet)** — mechanism proof. Migrated via controlled
  1r→2r(create-before-remove)→1r. **Process lesson:** scheduling changes mid-rebuild caused restarts
  (swift-mac→fast-skunk→star-kitten); *don't touch scheduling during an in-flight rebuild.* Landed on
  star-kitten (target is immaterial — throughput is target-independent). loving-gannet exposure 286→~256 Gi.
  **Decision: pause large-volume P2 at 0.9 GiB/min; do P1.6 (upgrade + benchmark) first — higher value
  than hand-moving ~100 Gi at current speed.**
