# Datastore Selection — CNPG vs plain StatefulSet vs external-managed (how to run a database)

**Choosing *how* a Postgres runs is a design decision with a real failure-mode consequence — not a
default.** On this cluster Postgres runs three ways, and they behave very differently when a node or a
Longhorn volume fails. This rule says which to pick. Companion: the ADR `docs/cnpg-standard.md` (CNPG is
the standard), `reliability-storage-tiering.md` (the storage tiers), `cloud-adoption.md` (the cloud gate),
`scheduling.md` (no node-pins). Scope: **Postgres** specifically; non-PG stores (Qdrant/ClickHouse/
MariaDB/Redis) have no CNPG option and follow the storage tiers directly.

## The governing rule (already set by the ADR)
> **CNPG is the DEFAULT for every Postgres we operate.** A plain StatefulSet is the *exception you must
> justify*, not a coin-flip; an external managed DB (Neon/RDS) is a *deliberate, gated* choice. New
> databases are born as a CNPG `Cluster`; raw/vendor StatefulSets are migration candidates (need-first).

## The three ways Postgres runs here

| Pattern | What it is | Durability lives in… | Gives you |
|---|---|---|---|
| **CNPG** (operator) | a `Cluster` CR: primary + streaming replica(s), automated failover | the **database layer** (app-level replication) | HA/failover · WAL **PITR** + R2 backups · tested restore drills · rolling upgrades |
| **plain StatefulSet** | a bare Postgres pod + a PVC, no operator | the **storage layer** (the single Longhorn volume) | simplicity, minimal footprint — and **nothing else** |
| **external managed** (Neon/RDS) | off-cluster SaaS Postgres | the **provider** | zero in-cluster footprint, scale-to-zero — at the cost of internet/DNS/provider dependency + latency + egress-netpol + sovereignty |

## The decision — the 10-second test
> **"If this volume vanished right now, is that an *incident* or a *shrug*?"**
> **Incident** (hard to regenerate, someone depends on it) → **CNPG.**
> **Shrug** (re-seed from migrations/seed and move on) → a plain StatefulSet is a justified exception.

Second filter: *"Must it stay up while a node is down?"* Yes → CNPG (failover). No → STS is allowed.

**Prioritise CNPG when ANY holds:** data is business/identity/financial or otherwise hard to regenerate ·
you need automated failover · you need PITR + off-site backup + *proven* restore (audit/DORA) ·
long-lived/production-like · **(this cluster specifically) it sits on flaky Longhorn and must survive
storage churn** — CNPG fails over at the DB layer instead of taking an outage (proven in the 2026-10
storage incident: CNPG DBs rode it out while single-copy raw-RWO volumes wedged).

**A plain StatefulSet is a justified exception ONLY when ALL hold:** data is ephemeral/dev/regenerable ·
single-instance is acceptable (no HA need) · low-stakes/short-lived/demo · you want to minimise footprint ·
*(or)* a vendor chart bundles its own PG and external-DB wiring isn't worth it yet. **Record the
exception** (one line in the app's docs/PR — why it's not CNPG).

## The sweet spot for THIS cluster — CNPG 2-instance + Longhorn RF=1
Flaky storage inverts the usual "single STS is fine" advice: the storage layer is exactly what fails here.
But naïve CNPG HA (2–3 instances × Longhorn RF=3) also *multiplies* the replica churn that wedges volumes.
The resolution (the **App-HA 1r** tier in `reliability-storage-tiering.md`): run **CNPG with 2 instances,
each on Longhorn `RF=1`** → two independent copies on two nodes at the **database** layer, *without*
stacking triple *block-level* replication underneath. App-level redundancy + minimal storage churn. Verify
the two instances land on **distinct, storage-healthy nodes** (anti-affinity) — a single copy on one node
is not resilience.

## External managed (Neon/RDS) — deliberate + narrow, never "move everything"
Reserve external-managed Postgres for cases where it genuinely adds value, each passing the
`cloud-adoption.md` gate (real need · justification · free-tier/in-cap · layer-routed · destroyable):
- a **demonstrated third-party-ICT / hybrid-cloud pattern** (DORA evidence — migrate *one* app to show it);
- **dev/ephemeral/scale-to-zero** workloads where sovereignty doesn't matter;
- **new** apps, need-first.
**Do NOT migrate the sovereign core** (claims/policy/underwriting/iam/authentik) off-cluster — it's EU-
sovereign, offline-capable, PITR-backed, you control it, and it's your strongest platform evidence.
Migrating already-resilient CNPG DBs to a US SaaS reverses a validated decision, weakens the sovereignty
thesis, and only *partially* relieves Longhorn (non-PG stores stay). See the 2026-10-17 analysis.

## Current placement audit (keep current)
- **Correctly on CNPG** ✅: authentik, synapse, claims, data-platform, langfuse, nextcloud, underwriting.
- **Plain STS but hold *prod business/identity* data → CNPG migration candidates** ⚠️ (posture checked
  2026-10-17): all single-**instance** alpine StatefulSets (no DB failover, no PITR), ~145–196 MiB each —
  they fail the 10-second test on the wrong side. Priority order by how exposed:
  **`ktayl-iam` (prod) is 🔴 urgent — Longhorn RF=1 *and* no backup CronJob → one volume wedge = total,
  unrecoverable loss of identity data**; `ktayl` + `retrieva` (prod) are 🟠 (RF=3 + a logical-dump
  CronJob, so recoverable, but no failover/PITR). Bring all three up to CNPG (2-instance / RF-1 shape).
- **Plain STS genuinely fine**: dev branches; vendor-coupled regenerable state (backstage catalog, plane
  demo) — exceptions recorded.

Related: `docs/cnpg-standard.md`, `reliability-storage-tiering.md`, `cloud-adoption.md`, `scheduling.md`,
`twelve-factor.md` (#4 backing services), `schema-erd.md`.
