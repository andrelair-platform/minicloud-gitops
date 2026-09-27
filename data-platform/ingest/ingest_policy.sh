#!/usr/bin/env sh
# Slice-1 ingestion: full-refresh copy of the 3 live policy tables → analytics.raw.*
# Decoupled (pg_dump data-only → psql), not FDW — the data platform keeps its own copy so it never
# couples to / loads the operational source. Small data → full refresh is fine; CDC (Debezium→NATS)
# is the Slice-2+ upgrade. All connection params via env (ESO-injected).
set -eu

: "${POLICY_PG_HOST:?}" "${POLICY_PG_USER:?}" "${POLICY_PG_PASSWORD:?}" "${POLICY_PG_DB:?}"
: "${ANALYTICS_PG_HOST:?}" "${ANALYTICS_PG_USER:?}" "${ANALYTICS_PG_PASSWORD:?}" "${ANALYTICS_PG_DB:?}"

SRC="postgresql://${POLICY_PG_USER}:${POLICY_PG_PASSWORD}@${POLICY_PG_HOST}:${POLICY_PG_PORT:-5432}/${POLICY_PG_DB}"
DST="postgresql://${ANALYTICS_PG_USER}:${ANALYTICS_PG_PASSWORD}@${ANALYTICS_PG_HOST}:${ANALYTICS_PG_PORT:-5432}/${ANALYTICS_PG_DB}"

echo "[ingest] ensuring raw schema + tables"
psql "$DST" -v ON_ERROR_STOP=1 <<'SQL'
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.policies  (id uuid, policy_number text, holder_name text, product_code text, status text, effective_date timestamptz, expiry_date timestamptz, created_at timestamptz, updated_at timestamptz);
CREATE TABLE IF NOT EXISTS raw.coverages (id uuid, policy_id uuid, type text, insured_amount bigint, deductible bigint);
CREATE TABLE IF NOT EXISTS raw.premiums  (id uuid, policy_id uuid, amount bigint, frequency text, due_date timestamptz, paid_at timestamptz);
SQL

for t in policies coverages premiums; do
  echo "[ingest] refreshing raw.$t"
  psql "$DST" -v ON_ERROR_STOP=1 -c "TRUNCATE raw.$t;"
  # stream rows source→dest via COPY (no temp file, no full table lock on source)
  psql "$SRC" -v ON_ERROR_STOP=1 -c "\copy (SELECT * FROM $t) TO STDOUT WITH (FORMAT csv)" \
    | psql "$DST" -v ON_ERROR_STOP=1 -c "\copy raw.$t FROM STDIN WITH (FORMAT csv)"
  psql "$DST" -tAc "SELECT '[ingest] raw.$t rows=' || count(*) FROM raw.$t;"
done
echo "[ingest] done"
