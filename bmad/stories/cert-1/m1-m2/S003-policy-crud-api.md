---
id: S003-policy-crud-api
title: "Policy REST API — CRUD endpoints + OpenAPI spec"
status: In Progress
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 5
labels: [go, api, openapi, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **souscripteur**, I want to create, read, and update insurance policies via a REST API so that the ktayl-portal and external systems can manage the policy lifecycle programmatically.

## Background

CdCF §6.1 (BF-POL-01 to BF-POL-05) defines policy management requirements. The API is consumed by ktayl-portal (BFF pattern) and by ktayl-claims-service (reads policy details on FNOL). OpenAPI spec is the contract artefact for BC02.

## Acceptance Criteria

- [ ] AC-1: `POST /v1/policies` — creates policy in DRAFT status, returns 201 + `{id, status, created_at}`
- [ ] AC-2: `GET /v1/policies/:id` — returns full policy with coverages and current premium; 404 if not found
- [ ] AC-3: `GET /v1/policies?holder_id=&lob=&status=&page=&limit=` — paginated list (max 100/page)
- [ ] AC-4: `PUT /v1/policies/:id` — updates mutable fields (effective_date, coverages, premium); rejects status transitions (handled by S004)
- [ ] AC-5: `DELETE /v1/policies/:id` — soft-delete (status → CANCELLED) only if DRAFT; 409 if ACTIVE
- [ ] AC-6: OpenAPI 3.1 spec at `api/openapi.yaml` — validated with `vacuum` linter, 0 errors
- [ ] AC-7: `GET /healthz` returns `{"status":"ok","version":"<sha>"}` with 200

## Technical Notes

- Router: `go-chi/chi/v5` with middleware: `RequestID`, `RealIP`, `Logger` (slog), `Recoverer`, `Timeout(30s)`
- Request validation: `github.com/go-playground/validator/v10` on request structs
- Error responses: RFC 7807 Problem Details (`application/problem+json`)
- All handlers in `internal/api/handlers/` — thin layer, delegate to domain service
- Domain service in `internal/domain/service.go` — business logic lives here, not in handlers
- Pagination: cursor-based on `created_at DESC` + `id` (no OFFSET — avoids large table scans)
- OpenAPI spec written by hand first, then validated — NOT generated from code (code follows spec)

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes
- [ ] L1: handler unit tests with `net/http/httptest` (happy path + 4xx cases per endpoint)
- [ ] OpenAPI spec passes `vacuum lint api/openapi.yaml`
- [ ] PR merged to `staging`
- [ ] REC-POL-01 partially covered (policy creation — full validation in S004 + S006)

## Tasks

- [ ] TASK-1: Write `api/openapi.yaml` (all 5 endpoints + schemas)
- [ ] TASK-2: Write `internal/api/handlers/policy_handler.go`
- [ ] TASK-3: Write `internal/domain/policy_service.go` (Create, Get, List, Update, Cancel)
- [ ] TASK-4: Write `internal/api/middleware/` (requestid, logger, error)
- [ ] TASK-5: Wire router in `cmd/server/server.go`
- [ ] TASK-6: Write handler unit tests (`internal/api/handlers/policy_handler_test.go`)
- [ ] TASK-7: Run `vacuum lint` and fix spec warnings

## Dependencies

- Depends on: S001 (scaffold), S002 (domain model)
- Blocks: S004 (state machine uses service layer), S007 (auth middleware wraps these routes), REC-POL-01
