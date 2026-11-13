# Runbook — Data Platform policy ingest: the `analytics_ro` read-only role

**Why this exists.** The `dp-ingest-policy` CronJob copies `raw.policies` from the live policy-service DB.
It authenticates as a dedicated **read-only** role `analytics_ro`. The old `ktayl-postgres` StatefulSet
created that role **imperatively**, so when policy-service migrated to CNPG (`ktayl-cnpg` in `ktayl-prod`)
the role was never recreated — and the stale `POLICY_PG_HOST` in Vault still pointed at the dead
`ktayl-postgres.ktayl-prod`. Result: the ingest silently loaded **0 policies** (the job exits 0 even when
`psql` fails), so `raw.policies` and everything downstream (`stg_policies`, the MDM dims, `policy_portfolio`)
were empty.

## What the GitOps change does (merged)

- **`services/ktayl-policy-service/helm/templates/cnpg.yaml`** — `analytics_ro` is now a CNPG **managed
  role** (declarative, recreated on any rebuild), its password from the `analytics-ro-cnpg-role`
  ExternalSecret (Vault `platform/data-platform/policy-pg-password`), and the CNPG ingress NetworkPolicy
  now allows the `data-platform` namespace in on `:5432`.
- **`platform/data/data-platform/04-pipeline.yaml` + `01-secrets.yaml`** — the ingest now points at
  `ktayl-cnpg-rw.ktayl-prod.svc.cluster.local` / `ktayl_policy` (host+db as **plain env**, version-controlled;
  only user+password stay in Vault). The stale `policy-pg-host` Vault key is no longer read.

## The TWO manual steps (not GitOps — run once after merge/sync)

CNPG reconciles managed roles **after** `initdb`, so `postInitApplicationSQL` can't grant to `analytics_ro`
(it doesn't exist at bootstrap). On the already-existing cluster the GRANTs are applied by hand, once.

**1. Set the role password in Vault** (the managed role + the ingest both read this key):
```bash
# a strong password; ESO syncs it to analytics-ro-cnpg-role (ktayl-prod) + dp-policy-source (data-platform)
R='<root token from Vaultwarden>'; V=https://vault.10.0.0.200.nip.io
PW=$(openssl rand -base64 24)
# merge the key into the existing platform/data-platform secret (don't overwrite siblings):
curl -sk -H "X-Vault-Token: $R" -X PATCH -H 'Content-Type: application/merge-patch+json' \
  -d "{\"data\":{\"policy-pg-password\":\"$PW\",\"policy-pg-user\":\"analytics_ro\"}}" \
  $V/v1/secret/data/platform/data-platform
```

**2. Grant read-only on the live DB** (CNPG sets the role's *password* from the secret; object GRANTs are ours):
```bash
ssh controller "kubectl --context default exec -n ktayl-prod ktayl-cnpg-1 -c postgres -- psql -U postgres -d ktayl_policy -v ON_ERROR_STOP=1 <<'SQL'
GRANT CONNECT ON DATABASE ktayl_policy TO analytics_ro;
GRANT USAGE ON SCHEMA public TO analytics_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_ro;
SQL"
```

## Verify end-to-end
```bash
# 1. role exists + can be authed by CNPG (managed role reconciled)
ssh controller "kubectl --context default exec -n ktayl-prod ktayl-cnpg-1 -c postgres -- psql -U postgres -d ktayl_policy -tAc \"select rolname from pg_roles where rolname='analytics_ro'\""
# 2. run the ingest → raw.policies should load (prod has ≥1 policy)
ssh controller "kubectl --context default create job -n data-platform dp-ingest-verify --from=cronjob/dp-ingest-policy"
ssh controller "kubectl --context default logs -n data-platform job/dp-ingest-verify | grep 'raw.policies rows='"   # expect rows=N>0
# 3. run dbt → the dims/mart fill
ssh controller "kubectl --context default create job -n data-platform dp-dbt-verify --from=cronjob/dp-dbt-build"
ssh controller "kubectl --context default exec -n data-platform dp-postgres-1 -c postgres -- psql -U postgres -d analytics -c 'select count(*) from business.dim_policy'"
# cleanup: kubectl delete job -n data-platform dp-ingest-verify dp-dbt-verify
```

## Notes
- **Least privilege:** `analytics_ro` is SELECT-only — the ingest never needs write. Do **not** reuse the
  `ktayl` app role (read-write) for the ingest.
- **Durability:** the managed role + grants are now captured (role in GitOps; grants here) → a cluster
  rebuild recreates the role, and this runbook re-applies the grants.
