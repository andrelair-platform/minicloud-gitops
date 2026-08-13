---
id: S009-integration-tests
title: "L2 integration test suite — testcontainers PostgreSQL + NATS"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, testing, integration, testcontainers, cert-1]
priority: Must
assignee: AndreLiar
---

## Story

As a **Tech Lead**, I want L2 integration tests running against a real PostgreSQL and NATS server so that the repository layer and event publisher are tested before any PR reaches `staging`.

## Background

Testing standard `testing.md` — L2 triggers on PR to `staging`. Uses `testcontainers-go` to spin up real infrastructure in Docker. No mocks for DB or NATS — the goal is to validate Flyway migrations, SQL queries, and JetStream stream creation work correctly. Runtime: < 15 min.

## Acceptance Criteria

- [ ] AC-1: `make test-integration` runs `go test ./tests/integration/... -tags integration -count=1` using `testcontainers-go` — no external infra required (Docker socket only)
- [ ] AC-2: PostgreSQL container (postgres:16-alpine) starts, all Flyway migrations run clean, and the suite exits 0
- [ ] AC-3: `policy_repository_test.go` covers: Create policy → Get by ID → List with filters → Update → state transition writes audit log row
- [ ] AC-4: NATS JetStream container (nats:2.10-alpine with `--jetstream`) starts; `nats_publisher_test.go` verifies events are published on the correct subject with CloudEvents 1.0 envelope
- [ ] AC-5: Each test function uses `t.Cleanup` to teardown containers — no shared state between test functions
- [ ] AC-6: CI job `test-integration` runs on PR to `staging` only (not `dev`), needs: `test-unit`

## Technical Notes

- Library: `github.com/testcontainers/testcontainers-go` v0.34+ (module `testcontainers-go/modules/postgres`)
- Build tag: `//go:build integration` on all L2 test files — prevents `make test` from picking them up
- Flyway migration: use `golang-migrate` library's `source/iofs` — run from `embed.FS` so no external binary needed in tests
- `tests/fixtures/policy_builder.go` provides test data shared with L1 (no duplication)
- GitHub Actions: runs on `ubuntu-latest` with Docker available (Docker socket is available natively in GH-hosted runners)
- DB DSN pattern: `testcontainers` exposes mapped port — construct DSN after `container.MappedPort(ctx, "5432")`
- Test timeout: add `-timeout 10m` flag

## Definition of Done

- [ ] Code implements all ACs
- [ ] L2 suite passes locally (`make test-integration`) with Docker running
- [ ] CI job `test-integration` green on a PR to `staging`
- [ ] Total L2 runtime < 10 min in CI

## Tasks

- [ ] TASK-1: Add `testcontainers-go` and modules to `go.mod`
- [ ] TASK-2: Write `tests/integration/helpers/pg_container.go` (start + migrate + DSN helper)
- [ ] TASK-3: Write `tests/integration/helpers/nats_container.go` (start JetStream + client helper)
- [ ] TASK-4: Write `tests/integration/policy_repository_test.go`
- [ ] TASK-5: Write `tests/integration/nats_publisher_test.go`
- [ ] TASK-6: Update `.github/workflows/ci.yml` — add `test-integration` job (PR to `staging` trigger)

## Dependencies

- Depends on: S002 (repository), S004 (state machine), S006 (NATS publisher), S008 (CI workflow exists)
- Blocks: PR merge to `staging`
