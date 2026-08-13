---
id: S002-domain-model
title: "Policy domain model — structs, PostgreSQL schema, Flyway migrations"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, database, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **Backend Developer**, I want the core domain model and database schema in place so that all API and event stories have a stable data layer to build on.

## Background

CdCF §9 defines the logical data model for Contrats. Key entities: Policy, Coverage, Premium, PolicyDocument. The service uses PostgreSQL 16 with Flyway-compatible migration files (versioned SQL, executed at startup via `golang-migrate`).

## Acceptance Criteria

- [ ] AC-1: `Policy` struct covers all fields from CdCF §9 (id UUID, holder_id, product_code, lob, status, effective_date, expiry_date, premium_amount, currency, created_at, updated_at)
- [ ] AC-2: `Coverage` struct: id, policy_id, coverage_type, limit_amount, deductible, conditions JSONB
- [ ] AC-3: `Premium` struct: id, policy_id, amount, frequency (MONTHLY/QUARTERLY/ANNUAL), next_due_date
- [ ] AC-4: Flyway migration `V1__init_schema.sql` creates tables with correct FK constraints, indexes on (holder_id, status, lob)
- [ ] AC-5: `Repository` interface defined in `internal/repository/policy_repository.go` (Create, FindByID, Update, ListByHolder)
- [ ] AC-6: PostgreSQL implementation satisfies the interface (`internal/repository/postgres/`)

## Technical Notes

- Use `github.com/google/uuid` for UUID generation
- Use `database/sql` + `github.com/lib/pq` (no ORM — domain logic stays in Go, not DB)
- Status enum stored as VARCHAR(32), validated at domain layer not DB layer
- JSONB for `conditions` allows flexible coverage terms without schema migrations per product
- Migration runner: `github.com/golang-migrate/migrate/v4` — run at service startup before HTTP listener
- Connection pool: `sql.DB` with `SetMaxOpenConns(25)`, `SetMaxIdleConns(5)`, `SetConnMaxLifetime(5m)`

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes
- [ ] L1: unit tests for domain validation (invalid status transitions rejected, required fields enforced)
- [ ] L2: repository integration test with testcontainers (covered in S009)
- [ ] PR merged to `staging`
- [ ] ArgoCD: n/a (S010)

## Tasks

- [ ] TASK-1: Write `internal/domain/policy.go` (structs + validation methods)
- [ ] TASK-2: Write `internal/domain/coverage.go`, `premium.go`
- [ ] TASK-3: Write `migrations/V1__init_schema.sql`
- [ ] TASK-4: Write `internal/repository/policy_repository.go` (interface)
- [ ] TASK-5: Write `internal/repository/postgres/policy_postgres.go` (implementation)
- [ ] TASK-6: Write `internal/repository/postgres/db.go` (connection pool setup + migrate runner)
- [ ] TASK-7: Unit tests for domain validation rules

## Dependencies

- Depends on: S001 (repo scaffold)
- Blocks: S003, S004, S008, S009
