---
id: S008-unit-tests
title: "L1 unit test suite — 70% coverage gate, golangci-lint CI"
status: Done
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 2
labels: [go, testing, ci, cert-1]
priority: Must
assignee: AndreLiar
---

## Story

As a **Tech Lead**, I want a CI-enforced unit test suite with ≥70% coverage on business logic so that regressions are caught before any code reaches `staging`.

## Background

Testing standard `testing.md` — Tier A repo, L0+L1 required on every push to `dev`. `make test` must run < 5 min with no external deps (no Docker, no network). Coverage is measured on `internal/` package only (excludes `cmd/`, `migrations/`, `api/`).

## Acceptance Criteria

- [ ] AC-1: `make lint` runs `golangci-lint run ./...` and exits 0 on clean code
- [ ] AC-2: `make test` runs `go test ./internal/... -count=1 -race` and exits 0
- [ ] AC-3: `make test-cov` adds `-coverprofile=coverage.out -covermode=atomic`; `go tool cover -func coverage.out` shows ≥70% total coverage on `internal/` packages
- [ ] AC-4: GitHub Actions CI job `lint` runs on every push to `dev` and every PR; `test-unit` runs after (needs: lint)
- [ ] AC-5: Test file naming mirrors module (`state_machine.go` → `state_machine_test.go`)
- [ ] AC-6: Zero use of `t.Skip()` or `//nolint` without inline justification comment

## Technical Notes

- `golangci-lint` config in `.golangci.yml` — enable: `errcheck`, `govet`, `staticcheck`, `revive`, `gocyclo` (max 10), `exhaustive` (for switch on Status enum)
- `go test -race` catches data races early — important for the NATS publisher goroutine (S006)
- Coverage target packages: `internal/domain/`, `internal/api/handlers/`, `internal/api/middleware/`
- Coverage does NOT need to reach 70% on `internal/repository/postgres/` at this stage (integration tests cover it in S009)
- Test data: use `tests/fixtures/` package (policy builders with sensible defaults)
- Mocking strategy: interface-based — `PolicyRepository` interface allows mock in unit tests without a DB

## Definition of Done

- [ ] `.golangci.yml` present and enforced in CI
- [ ] `Makefile` targets: `lint`, `test`, `test-cov`, `build`
- [ ] GitHub Actions workflow `.github/workflows/ci.yml` with `lint` + `test-unit` jobs
- [ ] Coverage ≥70% on `internal/` confirmed in PR
- [ ] L0 + L1 jobs pass in CI on `dev` branch

## Tasks

- [ ] TASK-1: Write `.golangci.yml`
- [ ] TASK-2: Write/update `Makefile` with `lint`, `test`, `test-cov` targets
- [ ] TASK-3: Write `tests/fixtures/policy_builder.go` (fluent builder for test policies)
- [ ] TASK-4: Write missing unit tests to reach 70%: state machine table tests, handler tests, middleware tests
- [ ] TASK-5: Write `.github/workflows/ci.yml` (lint → test-unit, triggered on push + PR)

## Dependencies

- Depends on: S001 (scaffold), S002–S007 (code to test)
- Blocks: PR merge to `staging` (coverage gate)
