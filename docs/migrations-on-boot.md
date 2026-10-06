# ADR — Database migrations: self-migrate on boot (keep, with a revisit trigger)

- **Status:** Accepted (2026-10-06) · **Owner:** SA/TL · **Scope:** all custom DB-owning services
- **Relates to:** 12-factor #9 (Disposability) + #12 (Admin processes); `schema-erd.md`; `testing.md`
  (the alembic-logging incident); `qa-gate.md`; `gitops.md` (Kargo release model).

## Context

A 12-factor review (2026-10-06) flagged that **every custom service runs its schema migrations as a
side-effect of process startup**, and that this is an *explicit, documented* platform standard — not an
accident. Confirmed across the fleet:

| Service | Mechanism (runs on boot) |
|---|---|
| ktayl-policy-service (Go) | `runMigrations()` in `cmd/server/main.go` (golang-migrate) — the cited reference for the standard |
| ktayl-underwriting (Python) | `app/db/startup.py` → `alembic upgrade head` in-process; its comment states the standard verbatim |
| ktayl-iam (NestJS/TypeORM) | `database.module.ts` `migrationsRun: true` |
| retrieva-backend (Drizzle) | `index.ts` → `runMigrations()` on boot |
| ktayl-core (Spring/Flyway) | Spring Boot auto-runs Flyway on boot |

**The 12-factor tension.** Strictly, migrations are an **admin/release process (#12)** that should run
**once per release**, not inside every app process; coupling them to boot also hurts **disposability
(#9)** (slower start; N replicas racing the same migration) and **concurrency (#8)**.

**What actually bit us.** The real production-class incident was **not** a replica race (all four
migrators take an advisory lock, so concurrent boots serialise safely) — it was an **in-process
side-effect**: alembic's `fileConfig()` (default `disable_existing_loggers=True`) **disabled every
logger** after the startup migration, so the live service emitted zero logs (see `testing.md`,
`qa-gate.md`). That is the concrete cost of running migration tooling *inside* the app process.

## Decision

**Keep self-migrate-on-boot as the default — for now.** It is a legitimate, pragmatic choice for a
resource-constrained, mostly 1–2-replica lab:

- the migration **always matches the running image** (same artifact → no "which release ran the
  migration?" skew — a real benefit under the Kargo immutable-artifact model);
- **no extra orchestration** (no PreSync hook Job — and we have scars there, see
  `[[feedback_argocd_job_sync_wedge]]`);
- the advisory lock makes concurrent-replica boots safe.

This ADR **records** that decision so it reads as intent, not oversight — and names the trigger + the
target pattern for when the trade-off flips.

## Revisit trigger — switch when ANY of these becomes true

1. A service genuinely needs **many replicas** and migration-on-boot adds meaningful startup latency or
   lock contention at scale.
2. We hit **another in-process-side-effect bug** of the alembic-logging class (migration tooling mutating
   app process state). *Underwriting is the one with a prior incident — it's the first candidate to move.*
3. A migration becomes **long-running / destructive** (a boot-time migration that can wedge a rollout, or
   that we'd want to gate/approve separately from the deploy).

## Target pattern when we DO switch — same-image `initContainer` (not a PreSync Job)

Run migrations in an **`initContainer` using the SAME image** as the app, with a `migrate` entrypoint
(e.g. iam's standalone `npm run db:migrate`; underwriting a `migrate` command; policy-service a
`-migrate` flag). The app container starts only after it completes.

- **Keeps** the "migration matches the image + env" benefit (same artifact, same ESO-injected config).
- **Removes** migration from the app process → fast startup, clean disposability, no in-process
  side-effects (factor #9/#12 satisfied).
- **Lower-risk than a PreSync hook Job** (no hook-finalizer/Replace wedge class). Each replica's
  initContainer still invokes `migrate`, but the advisory lock makes that a one-applies-rest-no-op.
- A **per-release Job** (Helm pre-upgrade hook / ArgoCD PreSync) is the "purest" #12 form but is deferred
  — the orchestration + our Job-wedge history don't pay off at current scale.

Every service already has, or can trivially expose, a standalone migrate entrypoint — ktayl-iam's
`db:migrate` runner (built for the ERD drift-check) is the reference shape; it's the same command an
initContainer would call.

## Consequences

- **Now:** no code changes; the standard is unchanged but documented, with a trigger + a pre-chosen
  low-risk path. The alembic `disable_existing_loggers` footgun is called out so it isn't re-introduced.
- **On trigger:** migrate the affected service to the initContainer pattern (start with underwriting),
  verify through the live QA gate, and update this ADR's status.
- This is a **security/architecture-boundary-adjacent** decision (deploy mechanics) → recorded here per
  the governance gate (`bmad-compliance.md`).
