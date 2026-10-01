# Longhorn Upgrade (1.6 → current) + Rebuild-Throughput Benchmark — Scoping

**Status:** Scoping (design only — no cluster mutation) · **Owner:** Platform · **Date:** 2026-10-01
**Parent:** reliability epic #1518 · **Driver:** P1.6 — rebuild throughput ~0.9 GiB/min is the MTTR ceiling.

Two **separate** workstreams (do not conflate — one variable at a time):
- **LH-UPGRADE** — get from 1.6 to a current release *safely*.
- **LH-BENCHMARK** — measure whether the new rebuild features actually improve *our* recovery.

## Current state (grounded 2026-10-01)
| Fact | Value |
|---|---|
| Longhorn | **v1.6.0** (manager + engine `ei-acb7590c`) |
| Kubernetes | **v1.36.3+k3s1** (uniform on all 6 nodes) |
| Data engine | **V1 on all 58 volumes** (no V2/SPDK) |
| Health | 0 faulted (1 degraded = the in-flight P2.1 rebuild) |
| Install method | **raw `kubectl apply` manifest** (no helm release; `last-applied-configuration` present). Only *settings* (`manifests/longhorn`) are GitOps-managed via the `longhorn-base` ArgoCD app. |

## ⚠️ Two scoping risks to resolve before scheduling

1. **k8s 1.36 is newer than the intermediate Longhorn versions' tested matrix.** The one-minor-at-a-time
   path (below) runs 1.7–1.12 on **k8s 1.36**, but those versions shipped before k8s 1.36 existed → they
   are **out-of-support-matrix in the middle of the path**. 1.6.0 itself is already well outside its matrix
   on k8s 1.36 (so we're *overdue*). **Mitigation:** check each hop's `support matrix` for max-k8s; where a
   hop doesn't list 1.36, accept it as untested-but-likely-working and lean hard on the per-hop health gate
   + rollback. (This is a strong argument to get current quickly — our k8s is ahead of our storage layer.)
2. **Upgrade method is manifest-apply, not helm/GitOps.** Each hop = `kubectl apply -f <version>/deploy/
   longhorn.yaml`. **Preflight action:** locate the authoritative install source (expected: the
   `minicloud-ansible` longhorn role or the pinned upstream URL) and drive the hops from there, recording
   the applied version. Consider migrating core to the **helm chart** *after* reaching current (separate
   change — not during the version climb).

## Staged version path (one minor per hop — Longhorn rule since 1.5)
```
1.6.0 → 1.7.x → 1.8.x → 1.9.x → 1.10.x → 1.11.x → 1.12.x → 1.13.x
```
(Pick the latest patch of each minor. 1.11 = scale/multi-source rebuild; 1.12 = V2 GA — **keep V1**; 1.13 = target.)

### Per-hop health gate (ALL must pass before the next minor)
```
[ ] longhorn-manager rolled out to the new version (all pods Ready)
[ ] all longhorn-system pods Ready (csi-*, instance-manager, driver-deployer, ui)
[ ] engine images reconciled/upgraded (new ei-* deployed, old drained)
[ ] 0 Faulted volumes, 0 stuck Degraded (allow transient rebuilds to finish)
[ ] CRDs upgraded cleanly (no conversion errors)
[ ] application smoke: NC 200, a CNPG read/write, Vault unsealed, NATS JS up
[ ] a Longhorn system backup taken (pre-hop)
```

## Preflight checklist (before hop 1)
```
[ ] P2.1 fully complete — NO rebuild running (wait for ClickHouse → 1r)
[ ] 0 faulted / 0 degraded volumes
[ ] no node cordons / drains / rebalances / eviction in progress
[ ] confirm install source + method (ansible role vs upstream URL)
[ ] per-hop k8s-1.36 compatibility checked against each version's support matrix
[ ] Longhorn system backup (settings + volume metadata) to R2/MinIO
[ ] critical app backups verified RESTORABLE (CNPG→R2 restore drill, not just "backup exists")
[ ] free disk headroom on every node for reconciliation (watch the loving-gannet 286 Gi node)
[ ] rebuild concurrency stays at 2 (committed) during the climb
[ ] maintenance window (each hop briefly disrupts the CSI/attach path)
```
> Longhorn explicitly: **do not upgrade with faulted volumes**, and take a backup first.

## Rollback gates
- **Per hop:** if the health gate fails, do **not** proceed; investigate. A Longhorn minor upgrade is not
  cleanly reversible (CRD schema moves forward), so rollback = restore from the pre-hop system backup +
  re-apply the previous version manifest. Treat each hop as commit-forward; the safety is the *gate*, not
  easy reversal.
- **Data safety:** volumes stay V1 + replicated; a failed *manager* upgrade doesn't destroy replica data.
  The risk is control-plane/CSI disruption, not block data — but verify attach/detach after each hop.

## LH-BENCHMARK protocol (run only AFTER reaching 1.13, V1 kept constant)
**Baseline (already measured on 1.6):** ~0.9 GiB/min, 30 GiB ≈ 33 min, single-source, RX ~15.7 MB/s, target iowait 0%.

**Controlled variable = Longhorn version, then the rebuild setting. Constants: V1 engine, hardware, test volume, node pairings.**

1. **Create a disposable 3r test volume** (e.g. 10–20 Gi, write known data) with replicas on 3 healthy
   nodes. This is the correct topology for multi-source rebuild (2 healthy sources remain when 1 is removed).
   *(ClickHouse's 1r→2r was NOT a valid multi-source test — only one source.)*
2. For each setting, **delete one replica** (2 healthy sources remain) → time the rebuild of the 3rd:

| Test | `replica-rebuild-concurrent-sync-limit` | Throughput | 30 Gi est | net MB/s | src CPU | src disk | dst disk |
|---|---|---:|---:|---:|---:|---:|---:|
| 1.6 baseline (single-source, from P1.6) | 1 | ~0.9 GiB/min | ~33 min | 15.7 | TBD | TBD | 13.5 |
| 1.13 A | 1 | TBD | TBD | TBD | TBD | TBD | TBD |
| 1.13 B | 2 | TBD | TBD | TBD | TBD | TBD | TBD |
| 1.13 C | 3 | TBD | TBD | TBD | TBD | TBD | TBD |

3. **Separately** benchmark fast-rebuild: `fast-replica-rebuild-enabled` + snapshot checksums
   (`snapshot-data-integrity`) — measure rebuild gain **vs** the CPU/IO cost of checksumming (it runs at
   unpredictable times). Don't enable alongside the sync-limit test (isolate the variable).
4. **Do NOT switch to the V2/SPDK data engine during this** (GA in 1.12) — that's a second major variable;
   evaluate V2 as its own future experiment.
5. Record the two-dimensional KPI after: `recovery ≈ worst-case-exposure ÷ measured-throughput`.

## Expected outcome / decision criteria
- If `sync-limit 2–3` materially raises throughput (network has 8× headroom: 15→up to ~125 MB/s), the
  worst-node recovery (`286 Gi ÷ throughput`) drops proportionally → set it as default.
- Multi-source helps **node-loss recovery of 3r criticals** (where ≥2 healthy sources exist) — exactly the
  286 Gi concern; it does *not* speed 1r→2r migrations (one source), so it won't change P2 migration time.
- Combine with P2 (lower exposure) for the multiplicative win.
