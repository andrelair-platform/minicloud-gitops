# Database Credential Storage — Vault is the source of truth (the discipline)

**Where a database password lives is a governed decision, not an accident of how the chart happened to
wire it.** On a regulated insurer (DORA/GDPR) every DB credential must have **one** source of truth, be
**backed up**, be **rotatable**, and **never** sit in git/an image/a ConfigMap. This rule states the
standard so a new database is wired right the first time, and names the current gaps. Companions:
`gitops.md` (ESO + ArgoCD SSA), `datastore-selection.md` (how a DB *runs*), `ops-runbooks` (controller
secret hygiene + break-glass).

## The model — two layers + a break-glass store (never conflate them)

| Layer | What | Where |
|---|---|---|
| **Runtime copy** (what pods + the DBeaver one-liner read) | a **Kubernetes Secret in the DB's own namespace** — *always* exists | CNPG → `<cluster>-app` (`kubernetes.io/basic-auth`: `username`/`password`/`dbname`, owned by the `Cluster`); plain/vendor → a named Opaque secret |
| **Source of truth** (where the password *comes from*) | **Vault `secret/platform/*` → ESO** (authoritative) | ESO renders the runtime Secret; edit Vault → it re-renders |
| **Human break-glass** (emergency admin login, SSO down) | **Vaultwarden** `controller-break-glass` + the age-encrypted Vault crown jewels on the controller | NOT the per-DB runtime creds — human emergency access only |

The `*-cnpg-r2` secrets you see next to a CNPG cluster are **R2 backup** credentials, not a DB login.

## The standard (MANDATORY for every NEW database)

> **Vault is the source of truth for every database credential. The in-namespace k8s Secret is a
> *rendered copy*, never the origin. Human break-glass is Vaultwarden. Nothing else.**

- **CNPG** → set the role password **declaratively from Vault**: an ESO `ExternalSecret`
  (`<cluster>-cnpg-role` / `<role>-role`, store `vault-backend`, from `secret/platform/*`) referenced by
  `spec.managed.roles[].passwordSecret.name`. The operator still maintains `<cluster>-app`, but the
  **password value traces to Vault** (reconciled by CNPG). **Do NOT ship a CNPG cluster whose only
  credential store is the operator-generated `-app` secret** — that password is a random value that
  exists nowhere else (not in Vault, not in a backup you control, not centrally rotatable).
- **Plain / vendor DB** (StatefulSet, bundled MariaDB/ClickHouse/etc.) → credential via an ESO
  `ExternalSecret` from Vault; the chart consumes the rendered k8s Secret. Never a chart default password,
  never a literal in values.
- **Never** commit a DB password to git (the `guard-write.py` hook blocks secret material), bake it into an
  image, put it in a ConfigMap, or drop it in a plaintext file on the controller (the only on-disk secrets
  allowed are the **age-encrypted** Vault crown jewels — `ops-runbooks`).
- **Rotation:** Vault-sourced → edit Vault → ESO re-renders → CNPG reconciles / restart the consumer.
  Operator-only (legacy) → via CNPG, with no central record — which is exactly why it's not the standard.
- **New-DB Definition of Done** (pairs with `conventions.md` / `schema-erd.md`): the credential ES from
  Vault exists, the runtime Secret renders, and the password is **not** operator-only.

## Current state (verified 2026-11-21) — and the gap to backfill

**✅ Vault-sourced (`managed.roles[].passwordSecret` → ESO → Vault):** `authentik`, `synapse (chat)`,
`dp-postgres (data-platform)`, `ktayl-iam` (prod), `langfuse`, `nextcloud`, `retrieva` — plus **all
plain/vendor DBs** (ai, backstage, temporal, bookstack, itsm/GLPI, erp/MariaDB, ktayl-iam-dev,
langfuse-clickhouse).

**⚠️ Operator-generated only — the gap (password lives *only* in `<cluster>-app`, not in Vault):**
`claims` (+prod), `ktayl-core` (+prod), `underwriting` (+prod), `paperless (ktayl-dms)`.

These are **accepted-with-revisit**, not an emergency — but three of them are **prod insurance domains**
(claims/underwriting/ktayl-core), so they rank first for backfill. **Backfill = opportunistic** (do it the
next time you touch the cluster, or as a small dedicated PR): add a `<cluster>-cnpg-role` ExternalSecret
from Vault + wire `spec.managed.roles[].passwordSecret` (mirror `retrieva-cnpg` / `langfuse-postgres`),
then the `-app` password traces to Vault. **Revisit trigger:** any of these needs a credential rotation, a
restore-from-Vault drill, or a DORA secret-management assertion → backfill it then, at the latest.

## Don't
- Don't treat the CNPG operator-generated `-app` password as a source of truth — it's a copy with no origin.
- Don't hardcode a DB password in a chart/values/image/ConfigMap, or commit one (the hook blocks it).
- Don't put per-DB runtime creds in Vaultwarden (that's human break-glass); don't put break-glass-only logins solely in Vault.
- Don't read the `-ro`/`-r` replica service for a write client, and don't confuse `*-cnpg-r2` (backup) with a DB login.

Related: `gitops.md` (ESO + the SSA `ignoreDifferences`), `datastore-selection.md` (CNPG vs STS),
`ops-runbooks` (controller secret hygiene + Vaultwarden break-glass), `schema-erd.md` / `conventions.md`
(new-DB DoD), docs map: `developer-platform/db-credentials`.
