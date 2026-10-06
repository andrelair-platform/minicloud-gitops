# ADR — CloudNativePG is the Postgres standard; migrate raw/vendor instances onto it

- **Status:** Accepted (2026-10-06)
- **Owners:** SA/TL (platform)
- **Related:** `.claude/rules/gitops.md` (ESO + SSA `ignoreDifferences`), `.claude/rules/scheduling.md`
  (no node pins — Longhorn is network-attached), the data-stores inventory
  (`minicloud-platform-docs` → `insurance-platform/data-stores-inventory`), `[[feedback_cnpg_backup_restore_ops]]`,
  `[[feedback_cnpg_repoint_wal_retention]]`.

## Context

PostgreSQL is the house relational standard, but it was deployed **three inconsistent ways**:

1. **CNPG operator** (preferred) — authentik, claims, underwriting, nextcloud, data-platform. Gives
   automated base+WAL backup to R2 (**PITR**), a managed role, HA-capable instances, PodMonitor metrics.
2. **Custom-base StatefulSet** `postgresql:18.4.0-noavx512` (+ pgvector) — `postgresql-ai`, `postgresql-synapse`.
   A single-instance raw STS on an image that **lives only in Harbor** (rebuilt without AVX512 for the
   older ThinkPads' pgvector SIGILL) → **no PITR**, and a **GC'd-image SPOF** (the image was GC'd out once
   and took litellm down 6 days — see the Harbor `postgresql*` always-retain rule in `ops-runbooks`).
3. **Plain / vendor StatefulSet** — ktayl-iam, policy-service, retrieva, backstage, plane, temporal,
   harbor-database. No PITR; backup posture varies.

A concrete risk surfaced for **Langfuse**: its metadata DB (projects / API keys / managed prompts /
users — the auth anchor the per-product LLMOps wiring depends on, `llmops.md`) lived as a database
**inside the shared `postgresql-ai` STS in the `ai` namespace**. That is three problems at once:
**(a)** no PITR for Langfuse metadata; **(b)** a cross-namespace coupling (`langfuse` ns depends on a DB
in `ai`); **(c)** the GC'd-image SPOF + noisy-neighbour of a *shared* instance.

## Decision

1. **CNPG (style 1) is the standard for every Postgres on the platform** that we operate (i.e. not a
   DB bundled inside an adopted vendor chart we don't control). New databases are born as a CNPG
   `Cluster`; existing raw/vendor instances are **candidates to migrate** as the need/benefit arises
   (backup/PITR, HA, removing a coupling), not a big-bang sweep.
2. **A dedicated DB per workload** — do not host one app's database inside another app's shared Postgres
   instance across namespaces. Shared instances re-introduce coupling + noisy-neighbour + a shared SPOF.
3. **Every CNPG cluster backs up to R2** (barman object store, `s3://minicloud-cnpg-offsite/<name>`,
   retention 14d) with a daily `ScheduledBackup`, a `PodMonitor`, and the stale-backup/unhealthy
   PrometheusRule — the authentik/nextcloud shape is the template.
4. **Stock image unless pgvector is needed.** Langfuse metadata is plain relational → the operator-default
   `cloudnative-pg/postgresql` image (PG 17.4, operator 1.25.1) is correct. The `-noavx512` custom base is
   only for pgvector workloads (`postgresql-ai`, `postgresql-synapse`) until those too are reconciled.

## First migration executed — Langfuse (2026-10-06)

Langfuse was moved off `postgresql-ai` onto a dedicated CNPG cluster `langfuse-postgres` in the
`langfuse` namespace, additively and with a gated cutover:

1. **Additive** (PR #1650) — created the `Cluster` + role/R2 `ExternalSecret`s + operator netpol
   (`allow-cnpg-operator` :8000/:5432 — without it default-deny-ingress drops the operator's status
   probe and the cluster never goes healthy) + daily `ScheduledBackup` + alerts. Verified healthy +
   `ContinuousArchiving=True` + an on-demand base backup landing in R2 **before** touching Langfuse.
2. **Data migration** — `pg_dump` (PG 18.4 source) → `psql` restore into the new cluster (PG 17.4),
   **0 errors, exact parity** (71 tables / 16 MB; 70 prompts, 166 models, 3 api_keys, 1 llm_api_key,
   2 projects). The dump is plain Prisma DDL (ENUM types + COPY data), no PG18-only features → the
   18→17 restore is clean. Connect over **TCP** (`-h 127.0.0.1`), not the unix socket — CNPG uses
   **peer auth** on the local socket (the OS user is `postgres`, not `langfuse`).
3. **Cutover** (PR #1651) — repoint `postgresql.host` in `helm-values/.../langfuse-values.yaml` to
   `langfuse-postgres-rw.langfuse.svc` → ArgoCD helm-upgrade rolls web+worker onto the new DB (the
   pod-roll *is* the cutover). The `langfuse` role password is the **same** Vault value
   (`platform/langfuse/db-password`) the chart already consumes → a pure host repoint, no credential
   change. New web pod logged "412 migrations, No pending migrations to apply" (zero schema drift),
   `/api/public/health` = 200, live app connections on the new cluster.
4. **Restore drill (the backup/restore "done" bar)** — recovered a throwaway cluster
   (`langfuse-restore-verify`) **entirely from the R2 backup** (`bootstrap.recovery` + an
   `externalClusters` barman store). **Gotcha:** the externalCluster's barman **`serverName` must be set
   to the SOURCE cluster name** (`langfuse-postgres`) — it otherwise defaults to the externalCluster's
   own `name` and the restore fails with **`no target backup found`**. The recovered cluster showed exact
   parity (70 prompts / 166 models / 3 api_keys / 2 projects / 71 tables) → the new cluster's R2 backups
   are proven recoverable. Drill cluster + its temp operator netpol deleted after.
5. **Cleanup (completed 2026-10-06, once the drill proved recoverability)** — with the data living in
   three places (live cluster + proven-recoverable R2 backup + the old copy), the old `langfuse` db +
   role were **dropped from `postgresql-ai`** and the now-dead `allow-langfuse-postgresql` netpol (ai ns)
   **removed** (PR #1654; ArgoCD pruned it). The general rule still holds — *don't* destroy the source
   the same hour you cut over (`[[feedback_cnpg_repoint_wal_retention]]`); here the destructive step was
   gated on the **restore drill passing**, not on wall-clock bake time.

## Second migration — Synapse / Matrix (2026-10-06)

Moved Matrix's DB off the `-noavx512` `postgresql-synapse` STS onto a dedicated stock CNPG cluster
`synapse-postgres` (chat ns, gitops #1657 additive + #1658 cutover). **Key verification that reframed the
whole noavx512 story:** nothing on `postgresql-synapse` *or* `postgresql-ai` actually has the **`vector`
extension** installed (RAG vectors live in Qdrant, not pgvector) — so the custom `-noavx512` base is a
historical artifact and **stock CNPG (PG 17.4) is correct for all of them**. Synapse-specific: bootstrap the
db with **`localeCollate: C` / `localeCType: C`** (Matrix hard-requires C collation). Data migrated at exact
parity (173 tables; users/devices/access_tokens match).

**⚠️ Incident — the stateful-media-PVC trap (postmortem).** The DB cutover itself was clean, but Synapse
*also* owns an **RWO Longhorn media PVC**, and the host-change rollout (RWO + `strategy: Recreate` + Longhorn's
slow cross-node detach) **wedged that volume's engine** (oscillating `attaching`↔`faulted`; the pod failed to
attach → ReplicaSet recreated it on another node → chased the volume → re-faulted). Recovery lessons (full
detail → `[[reference_cnpg_migration_playbook]]`):
- **Manual `kubectl scale`/`kubectl patch application` made it worse** — selfHeal **and the root app-of-apps**
  revert both faster than you act, each scale adding a Recreate roll = more churn. A ~2-min cutover became a
  ~40-min incident.
- **To hold a chart-managed workload at replicas=0 against selfHeal** (the ananace chart exposes no usable
  replica value), add `ignoreDifferences` on the Deployment `/spec/replicas` + `RespectIgnoreDifferences=true`
  to the **Application via git** (kubectl patches are reverted by the root app). Then `kubectl scale 0` sticks.
- A **wedged/faulted volume with healthy replicas = engine wedge from churn, not corruption**; it detaches
  clean at zero consumers. Delete stale k8s VolumeAttachments pinning a bad node; cordon the bad engine node.
- The media store was near-empty + non-critical (the real state is the DB) → **recreated the media PVC fresh**
  (reclaim=Delete removed the wedged volume; ArgoCD recreated it empty) → clean attach, no churn. Matrix healthy.
- **The lesson for the next migration: quiesce the workload BEFORE the host cutover** so the roll + RWO attach
  happen once, cleanly — don't cut over against a live rollout.

The old `postgresql-synapse` STS is kept as a **bake anchor (~24h)**, then deleted (its `synapse-logical-backup`
CronJob — now superseded by CNPG R2 PITR — is removed with it). That retires the first of the two noavx512
consumers.

## Consequences

- **+** Langfuse metadata now has PITR + a dedicated instance; the cross-ns coupling + shared-SPOF are gone.
- **+** One more instance on the standard → consistent backup/restore/monitoring (`[[feedback_cnpg_backup_restore_ops]]`).
- **−** One more Postgres pod (modest: 100m/256Mi req) — fits the `langfuse` footprint, no quota bump.
- **+** Synapse off `-noavx512`; **verified nothing uses pgvector** → the custom base is retireable with
  stock CNPG (no custom-image prerequisite, contrary to the earlier assumption).
- **Remaining debt (ordered):**
  - **`postgresql-synapse` STS** — redundant, **bake-pending deletion** (~24h anchor) → then it + its
    `synapse-logical-backup` CronJob are removed = **1 of 2 noavx512 consumers retired**.
  - **`postgresql-ai`** (the other noavx512 consumer — 6 DBs: openwebui, litellm, ragdb, vaultwarden,
    flowise, mlflow) → stock CNPG. Plan: **Vaultwarden its own CNPG** (cross-ns + break-glass), the 5 ai-ns
    apps a **shared stock `ai-postgres`**. Once both instances are off it → **delete the
    `minicloud-postgresql-noavx512` image + repo + its Harbor always-retain rule.**
  - Other raw/vendor instances (ktayl-iam, policy-service, retrieva, plane, temporal, backstage) → CNPG.
  - **Process change (from the synapse incident): for any workload with its own stateful RWO PVC, QUIESCE it
    (scale to 0 via a git `ignoreDifferences`/replica hold) BEFORE the host cutover** — never cut over against
    a live rollout. Migrate need-first, not as a sweep.

## Operate / verify

```bash
kubectl -n langfuse get cluster langfuse-postgres -o wide          # Cluster in healthy state
kubectl -n langfuse get scheduledbackup,backups.postgresql.cnpg.io # daily schedule + backups
kubectl -n langfuse logs deploy/langfuse-web | grep -i migration   # "No pending migrations to apply"
# restore drill (throwaway ns) — same pattern as the authentik/nextcloud CNPG restore proof
```
