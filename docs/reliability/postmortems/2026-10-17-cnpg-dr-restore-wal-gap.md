# Postmortem — CNPG R2 backups were not restorable (DR Game Day #1)  (2026-10-17, induced)

**Summary.** The first DORA Pillar-3 DR Game Day (scenario 08 — restore a CNPG cluster from its R2
object-store backup into a throwaway namespace) **failed**: the restore aborted with
`FATAL: WAL ends before end of online backup`. The base backups of all three recently-migrated CNPG
clusters (`ktayl-iam-cnpg`, `ktayl-cnpg`, `retrieva-cnpg`) **looked healthy** (`firstRecoverabilityPoint`
set, `ContinuousArchiving: True`) but **could not actually be restored** — "backups you can't restore
aren't backups." Root-caused, fixed, and re-verified the same session: all three now restore cleanly
(53–71s, full table parity). Zero production impact — the drill ran entirely in scratch namespaces;
the live DBs were never touched.

**SLO impact.** None live. The *latent* exposure was severe: DR RPO/RTO for the three business/identity
DBs was effectively **infinite** (unrecoverable) despite the SLO register claiming RTO 15–30m / RPO 24h.
Post-fix, measured restore = **iam 71s · ktayl 53s · retrieva 53s** — all well inside target RTO.

**Timeline (UTC, 2026-10-17).**
- ~12:05 — Game Day #1 launched: recovery `Cluster` bootstrapping `ktayl-iam-cnpg` from R2 into `dr-drill-iam`.
- 12:16 — recovery pod `FATAL: WAL ends before end of online backup`; job hit `BackoffLimitExceeded`.
- ~12:30 — root cause confirmed (idle-DB closing-WAL not archived).
- ~13:02 — fix validated on iam: fresh backup + `pg_switch_wal` → restore **71s, 7/7 tables parity**.
- ~13:10 — fix applied + drilled on ktayl (53s, 6/6) and retrieva (53s, 26/26).
- ~13:32 — confirmed `archive_timeout=5min` **alone is NOT sufficient** (plain backup still unrestorable after a 6-min wait) → a periodic WAL switch is a required control.

**Root cause.** The clusters are **near-idle** (identity/policy/DORA data, very low write volume). A
PostgreSQL base backup must have *all* WAL generated during the backup archived to reach a consistent
recovery point. On a near-idle DB, almost no WAL is produced, so the segment containing the backup's
*stop* record is never filled/rotated — and **`archive_timeout` does not force it out either** (confirmed
by test). The closing WAL therefore never reached R2, so every restore stopped short with
`WAL ends before end of online backup`. `firstRecoverabilityPoint` being set was misleading — it marks a
backup *start*, not a provably-restorable point.

**What worked.** The Game Day itself — this gap was invisible to every passive signal (archiving
"working", recovery point set, backups "successful"); only an *executed restore drill* exposed it.
Scratch-namespace restores gave zero blast radius. CNPG's recovery-from-object-store + the SLO/RTO matrix
gave clean measurement.

**What didn't.** (1) The initial post-migration backups were never restore-tested — they were assumed
good. (2) `archive_timeout` was wrongly assumed sufficient for idle DBs. (3) The first drill harness
verified parity too eagerly (before the primary accepted connections) and tore down the clone on an
ambiguous result — fixed in v2 (readiness wait + no teardown-until-confirmed).

**Fix (applied).** Fresh base backup **+ immediate `pg_switch_wal` (×2 + checkpoint)** forces the closing
WAL segment to archive → the backup becomes restorable. Applied + re-drilled on all three. `GRANT EXECUTE
ON FUNCTION pg_switch_wal()` added to each app role to enable a future automated switch.

**Action items.**
1. **Durable preventive control — periodic WAL-switch CronJob (REQUIRED, confirmed by test).** One per
   low-write CNPG cluster. Reliable design = exec `pg_switch_wal` **as `postgres` via local peer-auth**
   (`kubectl exec` from a scoped SA) — NOT app-role TCP, which fails due to CNPG managed-role password
   drift. Schedule ~hourly (+ shortly after the daily ScheduledBackup). Owner: SEC/SRE. **Status: pending (gitops).**
2. **Recurring DR drill (detective control).** Add scenario-08 restore drill to the quarterly Game Day
   rotation — it is the only thing that catches this class of regression. Reusable drill script committed.
3. **Correct the record:** `firstRecoverabilityPoint` set ≠ restorable. The programme's results-log must
   record *exercised-restore* evidence, not backup-exists signals.

**Evidence.** Recovery-pod log (`WAL ends before end of online backup`), post-fix restore logs
(iam 71s/7✓, ktayl 53s/6✓, retrieva 53s/26✓), archive_timeout-sufficiency test (FAIL). Reusable drill:
the scratch-namespace recovery-Cluster pattern. Gotcha recorded in `[[reference_cnpg_migration_playbook]]`.
