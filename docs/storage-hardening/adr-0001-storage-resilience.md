# ADR-0001 — Longhorn storage resilience on the 6-node ThinkPad cluster

- **Status:** PROPOSED (review draft — nothing executed). Supersedes nothing yet.
- **Date:** 2026-10-09
- **Deciders:** platform owner (review required)
- **Scope:** the Longhorn storage layer + the operational procedures around it. **Out of scope / explicitly
  deferred:** LOT E (the `apps/manifests` → `platform/storage` path migration) and any Longhorn version upgrade.
- **Evidence base:** `evidence-matrix.md` (claims E1–E19, confidence-labelled).

## Context
Two linked failure episodes (2026-10-08/09):
1. **Initiating wedge (E9):** a single volume (matrix-synapse) could not attach — its Longhorn engine
   `exit 2`'d in `startFrontend` because `tgtadm` could not clear a **stale iSCSI target** left on the node.
2. **Amplified cascade (E11–E14):** remediating that (and similar) by **physically rebooting nodes** triggered
   `node-down-pod-deletion-policy=delete-both-…` → a mass pod reschedule → the freshly-rebooted empty node
   became a scheduler magnet → a thundering herd of simultaneous engine-starts → transient
   `pthread_create: Resource temporarily unavailable` + attach timeouts → ~13–17 volumes cycling
   `attaching↔faulted`. Bulk pod-deletes re-clustered the herd (E14).

**What the evidence refutes (important):** the cascade was **not** a static resource-limit defect. The
instance-managers have **no** pids/mem/nproc ceiling and the node thread/mmap limits were nowhere near
exhausted (E1–E6). Therefore **"raise the instance-manager limit" is not a valid remedy** — there is no limit
to raise. The failure is a **congestion/thundering-herd** property of doing mass simultaneous attaches on
this hardware, **plus** a recoverability gap (no out-of-band power, E19) that forced the wrong tool (reboots).

**What the evidence supports:** CNPG-managed volumes (11/11) rode it out via app-level failover; **every one
of the 13 cycling volumes was a raw-RWO singleton** (E16). Data was never lost (E18).

## Decision (proposed, pending validation)
Adopt a **layered resilience strategy**, in priority order, where **each layer is a hypothesis to be
validated by `reliability-validation-plan.md` before it is trusted** — not assumed:

1. **D1 — Remediation discipline (operational, zero-infra, highest confidence).** Codify that Longhorn
   attach wedges are remediated by **cordon-and-move of the single affected pod** (E15), never by node
   reboots or bulk pod-deletes (E12–E14). This directly removes the cascade *trigger*. Confidence: high
   (cordon-and-move is CONFIRMED to work; reboots/bulk-ops are CONFIRMED to trigger the herd).
2. **D2 — Congestion controls (config, medium confidence, MUST validate).** Reduce simultaneous
   attach/rebuild pressure and stagger node re-admission so an empty node cannot draw the whole herd.
   Candidate knobs listed in the backlog; **effect is UNVERIFIED (open question 3)** → gated on V-C.
3. **D3 — Recoverability so reboots are rarely needed and never trap us (medium, MUST validate).**
   (a) boot-resilience so a reboot cannot hang pre-sshd; (b) out-of-band power (E19) so a genuinely hung
   node is recoverable without a site visit. Neither fixes the *attach congestion* — they reduce the need
   for, and risk of, the remediation that caused it.
4. **D4 — Blast-radius reduction for critical state (architectural, lower confidence, MUST validate).**
   Prefer app-level-replicated stores (CNPG) for critical DBs (E16) and reduce the number of
   single-replica raw-RWO consumers. **Not** asserted as a storage fix (E17): CNPG still rides Longhorn.

**We explicitly do NOT decide** to: raise IM limits (refuted, E6); add smart plugs *as a storage fix*
(they only help node recoverability); or mass-migrate to CNPG (unproven for the raw-RWO class). Those are
either rejected or demoted to validate-first candidates.

## Alternatives considered (with honest trade-offs & why not sufficient alone)
| Alt | What | Why considered | Trade-off / why not alone | Verdict |
|---|---|---|---|---|
| A0 | **Do nothing / accept** | Incident self-resolved w/o data loss; CNPG fine | Raw-RWO singletons remain a recurring firefight; a real node failure repeats it | Rejected as sole path |
| A1 | **Raise IM pids/thread limit** | The pthread error *looked* like a limit | **Refuted (E1–E6): no limit exists.** Would be a null change presented as a fix | **Rejected** |
| A2 | **Remediation discipline (D1)** | cordon-and-move worked; reboots/bulk-ops caused the cascade | Prevents the *trigger* but not the underlying congestion if a real multi-volume event occurs | **Accept (primary)** |
| A3 | **Congestion controls (D2)** | directly targets the thundering herd | Longhorn's attach-throttling knobs are limited; slower normal rebuilds; **effect unverified** | **Accept, gated on V-C** |
| A4 | **Graceful drain + staggered re-admission + revisit `node-down-pod-deletion-policy`** | removes the mass-reschedule + magnet | changing the policy alters failover semantics (pods may not auto-move on real node loss) | **Accept, gated on V-B/V-E** |
| A5 | **Out-of-band power (smart plug) + boot-resilience (D3)** | a hung node was unrecoverable remotely (E19) | does **not** touch attach congestion; hardware + home-automation dependency; smart plug can't force-off a laptop that runs on battery (see runbooks) | **Accept as recoverability layer, not a storage fix** |
| A6 | **Selective CNPG / fewer raw-RWO singletons (D4)** | CNPG rode it out (E16) | CNPG still on Longhorn (E17); migration effort + per-workload feasibility; not all state fits CNPG | **Accept as blast-radius layer, validate** |
| A7 | **Replace Longhorn for critical state (e.g., local-path + app replication, or external storage)** | removes network-attached-iSCSI fragility for some workloads | large architectural change; loses Longhorn HA/snapshot/backup; out of proportion now | **Deferred (record for future)** |
| A8 | **Upgrade Longhorn** | a newer version may improve attach behavior | **explicitly out of scope** per constraints; unverified it addresses this; upgrade is its own risk | **Deferred** |

## Failure domains (what each layer touches)
- **D1 operational:** no cluster state; changes human/agent behavior + a runbook. Failure domain: none.
- **D2 congestion config (Longhorn `settings.longhorn.io`):** cluster-wide Longhorn behavior → affects
  **all** volumes' rebuild/attach pace. Blast radius: high if wrong; reversible by setting revert.
- **D3 boot/power:** per-node (BIOS/UEFI, a plug). Blast radius: single node.
- **D4 CNPG/workload:** per-workload data migrations. Blast radius: the migrated workload only; **stateful
  → requires backup + a maintenance window** (see backlog preconditions).

## Rollback posture
- D1: revert the runbook/rule doc (pure docs/`.claude/rules`).
- D2: every Longhorn setting change is a single-field revert to the recorded prior value (captured in the
  backlog's "preconditions" as the baseline).
- D3: BIOS/boot-order and plug are physical/manual revert; no GitOps state.
- D4: CNPG migration has its own restore-from-backup rollback per workload.

## Consequences
- **Positive:** the recurring firefight is addressed at its true cause (remediation discipline + congestion),
  with the recoverability + blast-radius layers reducing future severity.
- **Negative / accepted:** D2 may slow normal rebuilds; D4 is incremental effort; some fragility of
  raw-RWO-on-consumer-hardware remains (A7 deferred).
- **This ADR is not final:** D2/D3/D4 are **adopted as candidates to validate**, not as proven fixes. The
  `reliability-validation-plan.md` must pass (with its stop-conditions) before each is trusted/standardised.

## Relationship to LOT E
LOT E (the Longhorn **path-only** migration in `apps/`/`manifests/`) is unrelated to this fragility (it does
not change runtime behavior) but **touches the same layer**. Sequencing: **D1 (discipline) first; the storage
layer confirmed stable; then D2–D4 validated; LOT E only once storage is quiescent** — per the original plan
that Longhorn goes last and quiet.
