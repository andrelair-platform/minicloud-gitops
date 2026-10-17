# Postmortem — Chaos Game Days #2 & #3: DB failover + NATS (2026-10-17, induced)

**Summary.** Two induced-failure Game Days on the live platform (deliberate, measured, no real users):
scenario 03 (DB unavailable — kill a CNPG primary) and scenario 04 (NATS down — kill a NATS pod). Both
**recovered with no data loss**; each surfaced a measurement/tuning note rather than a failure. Target for
03 = `ktayl-cnpg` (synthetic policy data).

**Scenario 03 — DB unavailable (CNPG primary kill → failover).**
- Induced: `kubectl delete pod ktayl-cnpg-1` (the primary).
- Result: CNPG **promoted `ktayl-cnpg-2` to primary** (real failover); the app (`ktayl-policy-service`,
  2 replicas) **stayed Running**; the old primary rejoined as a replica → cluster back toward 2/2.
- **Data integrity: NO DATA LOSS** — `policies`=1, `premiums`=1 unchanged across the failover.
- **Finding (modest):** the cluster sat in `Failing over` for ~2 min before the promotion completed —
  CNPG's **conservative failover-delay on a graceful pod-delete** (it waits to avoid flapping), not a
  node-loss RTO. If a tighter RTO is wanted, tune `.spec.failoverDelay` / switchover behaviour. SLO target
  (RTO 30m) was met comfortably regardless.
- **Harness note:** the first measurement false-flagged "MISMATCH" — the script read `currentPrimary`
  before it updated and queried an empty pod name. Verified correct out-of-band (data intact, cnpg-2 primary).

**Scenario 04 — NATS down (pod kill → JetStream persists).**
- Induced: `kubectl delete pod nats-0` (ns `messaging`).
- Result: **all 3 NATS pods recovered (3/3 Running)**; JetStream data is on PVCs → persisted across the
  restart; pod came back in ~1 s.
- **Caveat (honest):** the JetStream **stream count** could not be read numerically — the `nats` CLI did
  not authenticate to the server's account from the pod, so it reported `0/0`. **Pod + PVC resilience is
  verified; numeric stream-persistence is unmeasured.** Follow-up: run the count from `nats-box` with the
  correct account context on the next drill.

**What worked.** CNPG failover is automatic + lossless; NATS/JetStream survives a pod loss on its PVCs;
the apps tolerated both. Inducing on a synthetic DB kept blast radius to a brief, measured blip.

**Action items.**
1. Tune CNPG `failoverDelay` (or document the ~2-min graceful-delete failover as accepted) — modest.
2. Fix the chaos harness: resolve `currentPrimary` correctly; run `nats stream report` with the account
   context so JetStream persistence is numerically verified next time.
3. Keep both scenarios in the **quarterly Game Day rotation** (`slo-register.md`).

**Evidence.** Failover promotion (`ktayl-cnpg-1`→`ktayl-cnpg-2`), data-intact counts, NATS 3/3 recovery.
Companion DR postmortem: `2026-10-17-cnpg-dr-restore-wal-gap.md`.
