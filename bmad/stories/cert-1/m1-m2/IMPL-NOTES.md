# CERT-1 M1-M2 Sprint — ktayl-policy-service (Go)

## Context

The `ktayl-policy-service` repo was created 2026-08-13 with S001 (scaffold) and S002 (domain model) already
committed. S003–S010 (8 stories, 25 SP) remain. This plan implements them in dependency order, story by story,
each merged to `staging` via PR before moving to the next. The sprint gate is **REC-POL-01**: a complete
policy lifecycle (create → activate → generate attestation → cancel) callable from the Mac with a signed URL
returned by `/v1/policies/:id/documents/attestation`.

## Current State

| Story | Status | Evidence |
|---|---|---|
| S001 repo scaffold | ✅ Done | go.mod, cmd/, internal/, Dockerfile, CI, Makefile |
| S002 domain model | ✅ Done | domain structs, V1__init_schema.sql, postgres/* impls |
| S003 policy CRUD API | 🔴 Pending | router has only /healthz |
| S004 state machine | 🔴 Pending | no state_machine.go, no V2 migration |
| S005 document gen | 🔴 Pending | no pdf_generator or minio_store |
| S006 NATS publisher | 🔴 Pending | internal/events/doc.go placeholder only |
| S007 auth middleware | 🔴 Pending | no auth in router |
| S008 unit tests / lint | 🔵 Partial | basic tests exist; golangci-lint not in CI |
| S009 integration tests | 🔴 Pending | testcontainers not set up |
| S010 k8s manifests | 🔴 Pending | no ktayl ns in gitops, no ArgoCD app |

## PostgreSQL Decision

Dedicated `ktayl-postgres` StatefulSet in `ktayl` namespace, pinned to set-hog (same pattern as
postgresql-synapse). 5Gi Longhorn RWO PVC. Not sharing postgresql-ai (different SLO, different team).
Provisioned in S010 via `manifests/ktayl/01-postgres.yaml`.

## Dependencies / New Go Modules

Add to go.mod before S003:
- `github.com/go-playground/validator/v10` — request validation
- `github.com/golang-jwt/jwt/v5` — JWT parsing (S007)
- `github.com/MicahParks/keyfunc/v3` — JWKS cache (S007)
- `github.com/nats-io/nats.go` — NATS client (S006)
- `github.com/cloudevents/sdk-go/v2` — CloudEvents envelope (S006)
- `github.com/minio/minio-go/v7` — MinIO client (S005)
- `github.com/go-pdf/fpdf` — PDF generation, no CGO (S005)
- `github.com/nats-io/nats-server/v2` — embedded test server for unit tests (S006)
- `github.com/testcontainers/testcontainers-go` — L2 integration tests (S009)

---

## Implementation Sequence

### Phase 1: S003 — Policy CRUD API (5 SP)
**Branch:** `feat/s003-policy-crud-api` → PR to `staging`

New files in `ktayl-policy-service`:
- `api/openapi.yaml` — OpenAPI 3.1 spec (5 endpoints + schemas)
- `internal/domain/policy_service.go` — `PolicyService` struct; `Create`, `GetByID`, `List`, `Update`, `Cancel`; accepts `PolicyRepository` + `CoverageRepository` + `PremiumRepository` interfaces
- `internal/api/handlers/policy_handler.go` — chi handlers delegating to `PolicyService`; RFC 7807 error responses
- `internal/api/handlers/policy_handler_test.go` — httptest, mock repo (interface impl)
- `internal/api/middleware/logger.go` — move request logger out of router.go
- Update `internal/api/router.go` — wire `/v1/policies` route group + inject `PolicyService`
- Update `cmd/server/main.go` — init pgxpool, run golang-migrate, instantiate postgres repos, wire service → router
- `db/migrations/` already has V1. No new migration needed here.
- Add `golangci-lint` to `.github/workflows/ci.yml` (runs before `go test`)

Key patterns:
- Handler reads JSON body → validates with `validator/v10` → calls service → returns 201/200/404/409
- Pagination: cursor on `(created_at DESC, id)`, `?cursor=<base64>` query param, max 100/page
- `/healthz` updated to include `"version": "<sha>"` from `VERSION` env var set at build time in Dockerfile

### Phase 2: S004 — State Machine (3 SP)
**Branch:** `feat/s004-state-machine` → PR to `staging`

New files:
- `internal/domain/state_machine.go` — `Transition(current Status, event Event) (Status, error)` pure function; transition table as `map[Status]map[Event]Status`
- `db/migrations/V2__audit_log.sql` — `policy_audit_log(id, policy_id, from_status, to_status, actor_id, reason, occurred_at)`
- `internal/repository/audit_log.go` — `AuditLogRepository` interface
- `internal/repository/postgres/audit_log_postgres.go` — `InsertAuditLog(ctx, tx, log)` — takes `pgx.Tx` not pool (transactional)
- `internal/api/handlers/transition_handler.go` — `POST /v1/policies/:id/submit`, `/activate`, `/cancel`; `GET /v1/policies/:id/history`
- `internal/domain/state_machine_test.go` — table-driven, all 7 valid + ~10 invalid transitions

Key invariant: every transition = `BEGIN; UPDATE policies status; INSERT audit_log; COMMIT`. `actor_id` comes from `r.Context()` (S007 sets it; use empty string until S007 merges, then wire up).

Update `internal/domain/policy_service.go` to call `Transition()` and write audit row in same tx.

### Phase 3: S007 — Auth Middleware (3 SP)
**Branch:** `feat/s007-auth-middleware` → PR to `staging`

New files:
- `internal/api/middleware/auth.go` — JWKS fetcher via `keyfunc/v3` with 5-min TTL; validate signature + expiry; extract `sub` claim → store in `context.WithValue`
- `internal/api/middleware/authz.go` — `RequireScope(scope string)` middleware factory; parse `scope` claim (space-separated); return 403 if scope absent
- `internal/api/middleware/auth_test.go` — mock JWKS server via `httptest.NewServer`; 8 table-driven cases (valid token, expired, missing scope, wrong scope, etc.)

Update `internal/api/router.go`:
- Route group `/v1/` wraps all policy routes with `auth.ValidateJWT(jwksURL)` middleware
- Per-endpoint: `GET /*` adds `RequireScope("policy:read")`, `POST/PUT/DELETE` adds `RequireScope("policy:write")`
- `/healthz` explicitly excluded

Update `cmd/server/main.go` — read `AUTHENTIK_JWKS_URL` env, pass to router.

**Manual step** (documented in PR description): create Authentik OAuth2 provider (client credentials) + Application; save client_id/secret to Vault `secret/ktayl/policy-service/authentik`.

### Phase 4: S005 — Document Generation (3 SP)
**Branch:** `feat/s005-document-gen` → PR to `staging`

New files:
- `db/migrations/V3__documents.sql` — `policy_documents(id, policy_id, type, minio_key, created_at)`
- `internal/documents/pdf_generator.go` — `GenerateAttestation(p *domain.Policy, coverages []*domain.Coverage) ([]byte, error)` using `go-pdf/fpdf`; embed policy number, holder, product, dates, coverages, generated_at
- `internal/documents/minio_store.go` — `Store(ctx, policyID, data []byte) (key, presignedURL string, err error)`; object key `policies/{id}/attestation-{timestamp}.pdf`; presigned URL TTL from `DOCUMENT_URL_TTL` (default 1h)
- `internal/api/handlers/document_handler.go` — `POST /v1/policies/:id/documents/attestation`, `GET /v1/policies/:id/documents`; status guard (ACTIVE or AMENDED only)

MinIO bucket `policy-documents` created at service startup if not exists; lifecycle rule 7 years configured via mc/MinIO API (not gitops — done in code at startup with `minio-go BucketLifecycle API`).

### Phase 5: S006 — NATS Publisher (3 SP)
**Branch:** `feat/s006-nats-publisher` → PR to `staging`

New files:
- `internal/events/publisher.go` — `Publisher` struct; `Connect(natsURL, caCert string)`, `Publish(ctx, event cloudevents.Event) error` with 3x retry backoff (5s/25s/125s); stream `POLICY_EVENTS` created at startup
- `internal/events/policy_events.go` — one `Build*Event(p *domain.Policy) cloudevents.Event` per event type; source=`ktayl-policy-service`, type=`com.ktayl.policy.<event>`

Update `internal/domain/policy_service.go` — after `tx.Commit()` on each transition, call `Publisher.Publish()` asynchronously (goroutine; errors logged, not propagated to HTTP caller).

Update `/healthz` handler to include `"nats": "connected"|"disconnected"` based on `nc.IsConnected()`.

Update `cmd/server/main.go` — connect Publisher from `NATS_URL` + `NATS_CA_CERT` envs.

Unit tests: embedded `nats-server/v2` started in `TestMain`; assert event published with correct CloudEvents fields.

### Phase 6: S008 — Unit Tests + golangci-lint CI (2 SP)
**Branch:** `feat/s008-unit-tests` → PR to `staging`

(Most unit tests written inline with S003–S007; this story formalizes coverage gate and lint config.)

New files:
- `.golangci.yml` — enable: `govet`, `errcheck`, `staticcheck`, `unused`, `gocritic`, `gofmt`, `gosimple`, `ineffassign`, `misspell`. Exclude: `internal/repository/postgres` (generated SQL patterns trigger false positives from `errcheck` on row.Scan — add per-file nolint with comment)
- Update `.github/workflows/ci.yml` — add `golangci-lint-action@v7` as first step before `go test`; coverage gate targets `./internal/domain/...,./internal/api/...` only (excludes events, documents, repository)
- Add `make lint` target calling `golangci-lint run ./...`

Coverage target verification: state machine has 7 valid + 10 invalid transition test cases → domain package alone should exceed 70%.

### Phase 7: S009 — Integration Tests (3 SP)
**Branch:** `feat/s009-integration-tests` → PR to `staging`

New files under `tests/integration/`:
- `tests/integration/policy_test.go` — full lifecycle: `POST /v1/policies` → `POST /submit` → `POST /activate` → `GET /:id` → assert ACTIVE status → `POST /cancel` → assert CANCELLED
- `tests/integration/testmain_test.go` — `TestMain` starts `testcontainers-go` PostgreSQL 16 container + runs `golang-migrate`; starts embedded NATS server; starts `httptest.Server` running the full service
- `tests/integration/fixtures/` — shared policy request JSON fixtures

Add to `.github/workflows/ci.yml`:
- Job `integration-test` — runs only on PR to `staging`; after `test` job; uses `testcontainers-go` (Docker in GitHub Actions via `setup-buildx-action`)
- Prerequisite: `docker/setup-buildx-action@v3` before running integration tests

Add `make test-integration` target.

### Phase 8: S010 — k8s Manifests + ArgoCD Application (3 SP)
**Branch `feat/s010-k8s-manifests` in `minicloud-gitops`** → PR to `main`

**In `minicloud-gitops`:**

```
services/ktayl-policy-service/
  base/
    kustomization.yaml         # resources: deployment, service, serviceaccount
    deployment.yaml            # image: harbor.../ktayl-policy-service:latest (tag set by overlay)
    service.yaml               # ClusterIP :8080
    serviceaccount.yaml
  minicloud-1/
    dev/
      kustomization.yaml       # newTag: dev-<sha>, replicas: 1
    staging/
      kustomization.yaml       # replicas: 1, manual sync
    prod/
      kustomization.yaml       # replicas: 2
      ingress.yaml             # ktayl-policy.10.0.0.200.nip.io
      certificate.yaml         # minicloud-ca-issuer

manifests/ktayl/
  00-namespace.yaml            # namespace: ktayl
  01-postgres.yaml             # StatefulSet + Service + PVC (5Gi Longhorn, pinned set-hog)
  02-network-policies.yaml     # ingress from nginx; egress to postgres:5432, nats:4222, auth:443, minio:9000
  03-externalsecret.yaml       # ESO pulls DSN, NATS_URL, JWKS_URL, MINIO creds from Vault secret/ktayl/policy-service/

apps/workloads/ktayl-policy-service.yaml   # ArgoCD Application (auto-sync dev, manual staging/prod)
```

**Edit `manifests/argocd-project/00-project.yaml`** — add `ktayl` to destinations namespace list.

ESO pattern: same `ClusterSecretStore: vault-backend` as other apps. Add `ignoreDifferences` + `RespectIgnoreDifferences=true` per gitops.md mandate.

**In `ktayl-policy-service` repo:**
- Add `promote-dev` CI job — runs on push to `main`; uses `GITOPS_TOKEN`; runs `kustomize edit set image` in `services/ktayl-policy-service/minicloud-1/dev/` + commits

**Vault secrets to pre-populate** (manual step, documented in PR):
```
vault kv put secret/ktayl/policy-service/app \
  DSN="postgres://ktayl:***@ktayl-postgres.ktayl.svc.cluster.local:5432/ktayl_policy?sslmode=disable" \
  NATS_URL="nats://nats.nats.svc.cluster.local:4222" \
  AUTHENTIK_JWKS_URL="https://auth.10.0.0.200.nip.io/application/o/ktayl-policy-service/jwks/" \
  MINIO_ENDPOINT="minio.minio.svc.cluster.local:9000" \
  MINIO_ACCESS_KEY="..." \
  MINIO_SECRET_KEY="..."
```

---

## Branch + PR Strategy

| PR # | Branch | Target | Contains |
|---|---|---|---|
| PR-A | feat/s003-policy-crud-api | staging | S003 + golangci-lint to CI |
| PR-B | feat/s004-state-machine | staging | S004 |
| PR-C | feat/s007-auth-middleware | staging | S007 |
| PR-D | feat/s005-document-gen | staging | S005 |
| PR-E | feat/s006-nats-publisher | staging | S006 |
| PR-F | feat/s008-unit-tests | staging | S008 (.golangci.yml, CI gate) |
| PR-G | feat/s009-integration-tests | staging | S009 |
| PR-H | sprint-close | main | merge staging → main |
| PR-I | feat/s010-k8s-manifests | minicloud-gitops main | S010 |

S004 can start while S003 review is open (separate branch). S007 and S005 can start in parallel after S003 merges. S006 needs S004 done. S009 needs S003–S007 done.

---

## Sprint Gate — REC-POL-01

End-to-end smoke test from Mac (Tailscale connected):

```bash
BASE=https://ktayl-policy.10.0.0.200.nip.io
TOKEN=$(curl -s -X POST https://auth.10.0.0.200.nip.io/application/o/token/ \
  -d grant_type=client_credentials -d client_id=... -d client_secret=... \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 1. Create policy
POL=$(/usr/bin/curl --cacert ~/minicloud-ca.crt -s -X POST $BASE/v1/policies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"policy_number":"REC-POL-001","holder_name":"Jean Dupont","product_code":"IARD-AUTO-RC","effective_date":"2026-09-01T00:00:00Z","expiry_date":"2027-09-01T00:00:00Z"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Submit → activate
/usr/bin/curl --cacert ~/minicloud-ca.crt -s -X POST $BASE/v1/policies/$POL/submit -H "Authorization: Bearer $TOKEN"
/usr/bin/curl --cacert ~/minicloud-ca.crt -s -X POST $BASE/v1/policies/$POL/activate -H "Authorization: Bearer $TOKEN"

# 3. Generate attestation
/usr/bin/curl --cacert ~/minicloud-ca.crt -s -X POST $BASE/v1/policies/$POL/documents/attestation \
  -H "Authorization: Bearer $TOKEN"
# → {"document_id":"...","url":"http://minio.../...?X-Amz-Expires=3600","expires_at":"..."}

# 4. Cancel
/usr/bin/curl --cacert ~/minicloud-ca.crt -s -X POST $BASE/v1/policies/$POL/cancel \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason":"CUSTOMER_REQUEST","effective_date":"2026-08-16T00:00:00Z"}'

# 5. History
/usr/bin/curl --cacert ~/minicloud-ca.crt -s $BASE/v1/policies/$POL/history \
  -H "Authorization: Bearer $TOKEN"
# → 4 audit rows: draft→submitted, submitted→active, active→cancelled
```

All 5 calls must return 2xx. ArgoCD shows `ktayl-policy-service` Healthy+Synced.

---

## Issues to Close Per PR

- PR-A closes platform-backlog#250 (S001 — already done, close on first PR), #252 (S003)
- PR-B closes #253 (S004)
- PR-C closes #256 (S007)
- PR-D closes #254 (S005)
- PR-E closes #255 (S006)
- PR-F closes #257 (S008)
- PR-G closes #258 (S009)
- PR-I closes #259 (S010)
