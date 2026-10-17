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
- **`ktayl-iam` (prod) — ✅ MIGRATED to CNPG 2026-10-17** (was the 🔴 urgent case: RF=1 + no backup).
  Additive cluster → quiesced pg_dump→restore at exact parity → `DATABASE_HOST` drop-in flip →
  verified (backend 0 restarts, IAM 200, role rows match) → 2 instances + R2 PITR. STS kept until a
  soak, then retired. PRs: gitops #1810 (additive) · #1812 (Cluster ignoreDifferences) · #1813 (cutover).
- **`ktayl-policy-service` (prod) — ✅ MIGRATED to CNPG 2026-10-17** (was a 🟠 candidate: single-instance
  alpine STS, no failover/PITR). Additive `ktayl-cnpg` cluster (2 inst, R2 PITR) → healthy 2/2 →
  quiesced pg_dump→restore at parity (6 tables) → **cutover via an ESO DSN host-rewrite** (not a Vault
  edit — `secret/platform/ktayl-prod` needs break-glass root; the ops token has no access): the app's
  ExternalSecret `target.template` rewrites `ktayl-postgres`→`ktayl-cnpg-rw` (mergePolicy:Merge) →
  verified (2 live app conns on the CNPG primary, parity confirmed). **Follow-up (owner, non-urgent):**
  update the Vault DSN host + remove the ES template block (Vault back to single source of truth). STS
  kept until a soak, then retired. PRs: gitops #1815 (additive) · #1818 (CNPG netpol same-ns :5432) ·
  #1821 (ESO cutover). Gotcha: adding a `template` to a live ES is an **ArgoCD-SSA no-op** → delete the
  ES so it recreates WITH the template (the secret then re-renders rewritten).
- **`retrieva` (prod) — ✅ MIGRATED to CNPG 2026-10-17** (the last candidate: single-instance alpine STS,
  no failover/PITR). Additive `retrieva-cnpg` (2 inst, R2 PITR) with the same-ns `:5432` netpol **baked in
  from the start** (the ktayl #1818 lesson) → healthy **2/2 with no 1/2 stall** → parity (24 tables, 103KB
  dump) → flagship **quota bump** (req 2560→3200Mi/1→1.5cpu, lim 6→7.5Gi/6→7cpu, pods 16→18) → **cutover
  via the ESO `database-url` host-rewrite** (`retrieva-postgres`→`retrieva-cnpg-rw`, `index . "database-url"`
  for the hyphenated key, gated `cnpg.enabled`) → verified (4 live app conns on the CNPG primary — backend
  ×2 + worker). **Follow-up (owner, non-urgent):** update the Vault `database-url` host + remove the ES
  template. STS kept until a soak, then retired. PRs: gitops #1823 (additive+quota) · #1825 (ESO cutover).
  Note: `--clean` restore errors on Drizzle's `__drizzle_migrations` bookkeeping table are non-fatal.
- **AUDIT COMPLETE (2026-10-17): every prod business/identity Postgres is now on CNPG** (HA 2/2 + R2 PITR)
  — no remaining STS candidates holding prod data. Two cutovers used the **ESO host-rewrite** pattern
  (ktayl, retrieva) because `secret/platform/*` writes need break-glass root; iam used a clean values
  `DATABASE_HOST` flip. Open items: 2 Vault host edits (ktayl DSN + retrieva database-url) → then remove
  the 2 ES template rewrites; retire the 3 soaking STSes (ktayl-iam/ktayl/retrieva-postgres) to reclaim volumes.
- **Plain STS genuinely fine**: dev branches; vendor-coupled regenerable state (backstage catalog, plane
  demo) — exceptions recorded.

Related: `docs/cnpg-standard.md`, `reliability-storage-tiering.md`, `cloud-adoption.md`, `scheduling.md`,
`twelve-factor.md` (#4 backing services), `schema-erd.md`.
