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

### Version → k8s-1.36 support matrix (grounded 2026-10-01, resolves risk #1 with real numbers)
| Longhorn | k8s tested range | GA/EOL (Oct 2026) | Relevance |
|---|---|---:|---|
| 1.6.x | ~1.25–~1.28 | **EOL** | ← we are here; overshoots k8s by ~8 minors (works, unsupported) |
| 1.7.x / 1.8.x | ~1.28–~1.32 | **EOL** | transit hops — run briefly on 1.36 (overshoot) |
| 1.9.x | ~1.32–~1.33 | EOL 2026-11 | transit hop — overshoot |
| 1.10.x | ~1.33–~1.34 | EOL 2027-03 | transit hop — overshoot |
| **1.11.3** | **1.34–1.36** | EOL 2027-07 | **first to officially support k8s 1.36**; **floor** for multi-source rebuild (the throughput lever) |
| **1.12.1** | **1.33–1.36** | EOL 2027-08 | **latest stable** that lists k8s 1.36 |
| 1.13.0 | **≥1.34** (CSI external-provisioner v6.3.0) | GA, EOL 2027-11 | newest GA; also valid on 1.36 |

**No-skip-minor is enforced** (confirmed in the 1.12 upgrade docs): "if you … skip a minor version, the
operation will fail automatically." So the climb is strictly sequential; intermediate ceilings 1.7–1.10
are approximate (re-verify each hop's own matrix at execution) but the **shape is certain** — every hop
1.7→1.10 transits a k8s newer than it was tested on, the same overshoot we already run stably on 1.6.

**Target recommendation:** **1.12.1** (latest *stable* that lists k8s 1.36) = **6 hops**. 1.11.3 is the
*floor* (first with the throughput lever + first to support 1.36); 1.13.0 (a 7th hop) is valid but newer/
less-proven — defer it. Owner decision (target + in-place-climb vs reinstall-at-1.12.1) stays open.

## Staged version path (one minor per hop — Longhorn rule since 1.5)
```
1.6.0 → 1.7.x → 1.8.x → 1.9.x → 1.10.x → 1.11.x → 1.12.x  [recommended target]  (→ 1.13.x optional)
```
(Pick the latest patch of each minor. **1.11 = multi-source rebuild — the throughput lever, so ≥1.11 is
mandatory for LH-BENCHMARK**; 1.12 = latest stable + V2 GA — **keep V1**; 1.13 = optional newest GA.)

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

## Backup/restore readiness — drill evidence (2026-10-01, the #1521 precondition)

**Mechanism PROVEN** via a non-destructive restore drill: recovered `authentik-cnpg` into a throwaway
`restore-drill` namespace **purely from Cloudflare R2** (`s3://minicloud-cnpg-offsite/authentik`, read-only
against the source) — base backup downloaded + **WAL replayed from archive** → cluster healthy.
- **RTO:** ~9 min (543s) for a 167 MB DB · **RPO:** continuous WAL (last successful base backup 04:01 UTC
  that day; recoverability back to 2026-09-26) → point-in-time recovery to within minutes.
- **Data integrity:** restored `authentik_core_user` = **23 rows = source exactly**; DB size 167 MB = source.
- Source untouched; drill namespace deleted after.

**But the FLEET is not restore-ready — the real blocker (fix before the climb):**
| CNPG cluster | State | Action |
|---|---|---|
| authentik | ✅ proven restorable (drill) | none |
| nextcloud | ✅ **FIXED 2026-10-01** — recoverability point 11:23:53Z | none (see gotcha below) |
| **claims · claims-prod · underwriting · data-platform** | ❌ **no backup configured at all** | **add** barmanObjectStore + ScheduledBackup (mirror authentik) |

**nextcloud fix (gotcha — CNPG "Expected empty archive"):** WAL archiving failed with
`barman-cloud-check-wal-archive … Expected empty archive`. **Cause:** the CNPG migration re-created the
cluster, leaving **2 orphan WAL files** (`…000001.gz`, `…000002.gz`) under `s3://minicloud-cnpg-offsite/
nextcloud/nextcloud-postgres/wals/` with **no base backup**; CNPG's first-WAL safety guard (destination
must be empty for a fresh server) then tripped forever. **Not** a credential/path error — the connection
worked. **Fix:** `aws s3 rm … --recursive` the stale server prefix (verified: only orphan WALs, 0 base
backups, `firstRecoverabilityPoint=none` → nothing restorable lost) → `pg_switch_wal()` → archiving went
`True/ContinuousArchivingSuccess` → on-demand base backup → recoverability established. **R2 note:** aws
cli needs `AWS_DEFAULT_REGION=auto` (R2 rejects `eu-west-1`). The cluster's barmanObjectStore config was
already correct → runtime cleanup only, no GitOps change.

Longhorn block: 16/58 in the backup group; non-CNPG criticals **qdrant** (retrieva RAG vectors) + **n8n**
(workflows) are unprotected at both layers → add to the backup group. Vault = own raft snapshot (ok);
observability (loki/tempo/langfuse) = accepted loss.

> **Gate:** the per-hop rollback (restore from the pre-hop backup) is only real for clusters that have a
> verified backup. Until the five above are fixed + spot-drilled, the climb's safety net is incomplete.

### Remediation design (owner-approved 2026-10-01) — per-cluster R2 isolation
- **Per-cluster bucket + per-cluster token** (real Cloudflare-enforced isolation; bucket-level is the only
  scope R2 Object-R&W tokens enforce). Buckets created: `cnpg-underwriting-prod`, `cnpg-claims-prod`,
  `cnpg-claims`, `cnpg-data-platform`. Supersedes the current shared-key-on-one-bucket posture
  (authentik+nextcloud share the account R2 key via prefixes).
- **Token:** Account API token, **Object Read & Write, scoped to exactly one bucket.** Long-lived is
  acceptable operationally **but not "no expiry" forever** — **rotation policy: every 90–180 days**
  (scheduled), revocable per-incident. Minting requires the Cloudflare dashboard / an API-Tokens:Edit
  token (not automatable with our ops creds — owner mints the 4).
- **Flow:** R2 token → **Vault** `secret/platform/cnpg-r2-<db>` (write via `read -s`, never on the command
  line; operator identity over root) → **ESO** ExternalSecret → namespace Secret → CNPG `barmanObjectStore`.
- **Future (security backlog, NOT now):** Cloudflare **temporary R2 credentials** (bucket/prefix-scoped,
  ≤7-day TTL) via a credential-broker/rotation controller — replaces permanently-held S3 secrets once such
  a broker exists. Don't add that complexity to CNPG yet.

### Per-cluster verification gate (ALL required before moving to the next DB — not "secret exists")
```
[ ] ExternalSecret Ready            [ ] ScheduledBackup succeeds
[ ] CNPG sees credentials           [ ] base backup visible remotely (correct bucket)
[ ] WAL archiving = healthy         [ ] recoverability point established
[ ] first WAL object in the bucket  [ ] no archive-command failures
```
Rollout order: **underwriting → claims-prod → claims → data-platform**, then the **underwriting isolated
restore drill** (proves the mechanism against the business-critical config, as authentik proved the
mechanism generally). **U0 Recovery Gate = PASS only after all four + the underwriting drill are green.**

## Rollback gates
- **Per hop:** if the health gate fails, do **not** proceed; investigate. A Longhorn minor upgrade is not
  cleanly reversible (CRD schema moves forward), so rollback = restore from the pre-hop system backup +
  re-apply the previous version manifest. Treat each hop as commit-forward; the safety is the *gate*, not
  easy reversal.
- **Data safety:** volumes stay V1 + replicated; a failed *manager* upgrade doesn't destroy replica data.
  The risk is control-plane/CSI disruption, not block data — but verify attach/detach after each hop.

## LH-BENCHMARK protocol (run only AFTER reaching ≥1.11 — where multi-source rebuild lives; V1 kept constant)
**Baseline (already measured on 1.6):** ~0.9 GiB/min, 30 GiB ≈ 33 min, single-source, RX ~15.7 MB/s, target iowait 0%.

**Controlled variable = Longhorn version, then the rebuild setting. Constants: V1 engine, hardware, test volume, node pairings.**

1. **Create a disposable 3r test volume** (e.g. 10–20 Gi, write known data) with replicas on 3 healthy
   nodes. This is the correct topology for multi-source rebuild (2 healthy sources remain when 1 is removed).
   *(ClickHouse's 1r→2r was NOT a valid multi-source test — only one source.)*
2. For each setting, **delete one replica** (2 healthy sources remain) → time the rebuild of the 3rd:

| Test | `replica-rebuild-concurrent-sync-limit` | Throughput | 30 Gi est | net MB/s | src CPU | src disk | dst disk |
|---|---|---:|---:|---:|---:|---:|---:|
| 1.6 baseline (single-source, from P1.6) | 1 | ~0.9 GiB/min | ~33 min | 15.7 | TBD | TBD | 13.5 |
| target (≥1.11) A | 1 | TBD | TBD | TBD | TBD | TBD | TBD |
| target (≥1.11) B | 2 | TBD | TBD | TBD | TBD | TBD | TBD |
| target (≥1.11) C | 3 | TBD | TBD | TBD | TBD | TBD | TBD |

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
