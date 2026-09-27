# ktayl Data Platform — Slice 1 (Policy Portfolio)

Board **#5 (Data Platform)**. This is the **first thin vertical slice** of the analytical data platform,
built the way the [EA blueprint doctrine](https://andrelair-platform.github.io/minicloud-platform-docs/insurance-platform/enterprise-architecture-blueprint) prescribes: **one real live source → just-enough medallion → one data product → BI.**
It is deliberately *not* a generic connector framework or an OLAP cluster for sources that don't exist yet.

> Two-layer model: this is the **ktayl-solution IS** (the insurer). Not Retrieva, not a certification deliverable.

## What Slice 1 delivers

```
ktayl-policy-service (LIVE Postgres — the only fully-live business source)
        │  ingest/ingest_policy.sh  (full-refresh COPY; CDC later)
        ▼
   raw.*              →  dbt staging (curated schema)  →  dbt marts (business schema)
   policies/coverages/   stg_policies / stg_premiums /     policy_portfolio  ◄── the data product
   premiums              stg_coverages
        ▼
   Metabase dashboard: Policy Portfolio (GWP proxy · TIV · counts by LOB/status/inception)
```

**Data product `policy_portfolio`** (grain = policy) — grounded on real source columns only:
- `annualised_premium_eur` — GWP proxy (Σ installment × cadence ÷ 100). *Seeds P2 (margin/portfolio).*
- `total_insured_amount_eur` — TIV. *Seeds P1/P3 (exposure/accumulation).*
- `scheduled_premium_eur`, `paid_premium_eur`, `coverage_count`, dims: `product_code`, `status`, `inception_year`.

## Stack (light-first, fits the constrained cluster)

| Layer | Tool | Note |
|---|---|---|
| Storage (medallion) | **Postgres** (CNPG `analytics`), schemas `raw`/`curated`/`business` | own DB (no shared operational DB — ADR-005) |
| Ingestion | **CronJob** `ingest/ingest_policy.sh` (pg_dump→psql COPY) | full-refresh; CDC (Debezium→NATS) is Slice-2 |
| Transform | **dbt-postgres** (`dbt/`) — staging→marts + schema tests | run via CronJob after ingest |
| BI / serve | **Metabase** | Authentik SSO, reads `business` schema |

ClickHouse/Trino deferred until a real volume/perf need (need-first gate).

## Layout

```
data-platform/
  dbt/            dbt project (dbt_project.yml, profiles.yml, models/staging, models/marts)
  ingest/         ingest_policy.sh (source→raw)
  README.md       this
```

## Run locally (against a dev analytics Postgres)

```bash
# env: ANALYTICS_PG_* + POLICY_PG_*
sh ingest/ingest_policy.sh                 # land raw.*
cd dbt && dbt deps && dbt build            # staging→marts + tests (build = run + test)
```

## Run the pipeline in-cluster (on demand, not just the 02:00/02:30 cron)

```bash
kubectl create job -n data-platform dp-ingest-manual --from=cronjob/dp-ingest-policy   # prod → raw
kubectl create job -n data-platform dp-dbt-manual    --from=cronjob/dp-dbt-build        # raw → staging → business.policy_portfolio
kubectl exec -n data-platform dp-postgres-1 -- psql -U postgres -d analytics \
  -c "SELECT * FROM business.policy_portfolio;"                                          # verify
```

## Metabase — one-time UI setup (SSO is a follow-up; internal Tailscale-gated for now)

URL: **https://metabase.10.0.0.200.nip.io** (needs Tailscale + the minicloud CA trusted). The pod runs
in `data-platform`; its own metadata DB is the `metabase` database on the `dp-postgres` CNPG cluster
(auto-created via the `Database` CR, creds from Vault `secret/platform/data-platform`).

1. **First visit** → create the admin account (Metabase's own login for now).
2. **Add the analytics database** as a data source:
   - Type **PostgreSQL** · Host `dp-postgres-rw.data-platform.svc.cluster.local` · Port `5432`
   - Database `analytics` · User `analytics` · Password = Vault `secret/platform/data-platform` → `analytics-password`
   - Schemas to expose: **`business`** (the serve layer; `curated`/`raw` are internal).
3. **Build the Policy Portfolio dashboard** over `business.policy_portfolio` (grain = policy):
   - GWP proxy = `sum(annualised_premium_eur)` · TIV = `sum(total_insured_amount_eur)`
   - policy count by `status` / `product_code` / `inception_year`
4. The seeded demo row `TEST-DP-SLICE1-001` (GWP €12,000 · TIV €1,000,000) is kept so the dashboard has data before real prod policies exist.

**TODO (hardening):** put Metabase behind Authentik SSO (forward-auth or Metabase OIDC) instead of its
local admin; re-add restricted egress via a CiliumNetworkPolicy (`toEntities: [kube-apiserver, world]`).

## Assumptions to confirm with the Policy domain (before treating metrics as authoritative)

1. **Minor units** — `amount`/`insured_amount` are BIGINT; assumed **cents** (÷100 → EUR). Confirm.
2. **Premium semantics** — are `premiums` rows **installments** (annualise = ×cadence) or a single annual figure? The GWP-proxy annualisation assumes installments; confirm before it's the official GWP.

## Next (Slice 1 → deployable → Slice 2)

- **Deploy (next PR):** `data-platform` namespace + quota · CNPG `analytics` cluster (+ AppProject sourceRepos/destination/namespaceResourceWhitelist + the cnpg ingress netpol — see [[feedback_cnpg_onboarding_gotchas]]) · ESO secrets (policy + analytics creds) · ingest + dbt CronJobs · Metabase Helm app · ArgoCD apps. Then verify raw→marts→dashboard live.
- **Slice 2:** add a second real source when the next domain ships; generalise the ingestion from 2–3 real pipelines (never a generic framework up-front). CDC over batch. Add MDM-keyed Customer 360 once MDM exists.
