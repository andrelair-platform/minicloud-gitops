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
4. **Cleanup (bake-gated follow-up)** — the old `langfuse` db on `postgresql-ai` + the now-unused
   `allow-langfuse-postgresql` netpol (ai ns) are **kept briefly as a rollback anchor** (repoint `host:`
   back), then dropped once the new cluster is proven stable. Don't destroy the source the same hour you
   cut over (`[[feedback_cnpg_repoint_wal_retention]]`).

## Consequences

- **+** Langfuse metadata now has PITR + a dedicated instance; the cross-ns coupling + shared-SPOF are gone.
- **+** One more instance on the standard → consistent backup/restore/monitoring (`[[feedback_cnpg_backup_restore_ops]]`).
- **−** One more Postgres pod (modest: 100m/256Mi req) — fits the `langfuse` footprint, no quota bump.
- **Remaining debt (ordered candidates):** the other raw/vendor instances (ktayl-iam, policy-service,
  retrieva, plane, temporal, backstage) → CNPG; the `-noavx512` pgvector instances (`postgresql-ai`,
  `postgresql-synapse`) need a CNPG image with the custom base (or the pgvector-vs-Qdrant consolidation
  ADR) before they can move. Migrate need-first, not as a sweep.

## Operate / verify

```bash
kubectl -n langfuse get cluster langfuse-postgres -o wide          # Cluster in healthy state
kubectl -n langfuse get scheduledbackup,backups.postgresql.cnpg.io # daily schedule + backups
kubectl -n langfuse logs deploy/langfuse-web | grep -i migration   # "No pending migrations to apply"
# restore drill (throwaway ns) — same pattern as the authentik/nextcloud CNPG restore proof
```
