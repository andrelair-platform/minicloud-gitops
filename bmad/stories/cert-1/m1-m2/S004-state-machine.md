---
id: S004-state-machine
title: "Policy state machine — transitions, validation, audit log"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, domain-logic, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **souscripteur**, I want policy status transitions to be strictly validated so that a policy can only move between valid states, and every transition is recorded for DORA Art.9 audit traceability.

## Background

CdCF §6.1 BF-POL-03 defines the state machine. DORA Art.9 requires every business decision to be traceable. The audit log table records who triggered each transition, when, and the reason code — this is the primary compliance artefact for the jury.

## Acceptance Criteria

- [ ] AC-1: Valid transitions enforced — invalid transitions return 409 Conflict with reason
  ```
  DRAFT      → SUBMITTED (souscripteur submits for underwriting review)
  SUBMITTED  → ACTIVE    (underwriter approves)
  SUBMITTED  → REJECTED  (underwriter rejects)
  ACTIVE     → AMENDED   (PUT /v1/policies/:id/amend)
  AMENDED    → ACTIVE    (amendment confirmed)
  ACTIVE     → CANCELLED (POST /v1/policies/:id/cancel, reason required)
  ACTIVE     → EXPIRED   (automatic on expiry_date, triggered by batch)
  ```
- [ ] AC-2: `POST /v1/policies/:id/submit` — DRAFT → SUBMITTED
- [ ] AC-3: `POST /v1/policies/:id/activate` — SUBMITTED → ACTIVE
- [ ] AC-4: `POST /v1/policies/:id/cancel` — ACTIVE → CANCELLED (body: `{reason, effective_date}`)
- [ ] AC-5: `policy_audit_log` table created in `V2__audit_log.sql` (policy_id, from_status, to_status, actor_id, reason, occurred_at)
- [ ] AC-6: Every transition writes one row to `policy_audit_log` within the same DB transaction
- [ ] AC-7: `GET /v1/policies/:id/history` returns ordered audit log

## Technical Notes

- State machine implemented as a pure function: `func Transition(current Status, event Event) (Status, error)`  — no side effects, fully unit-testable
- Transition table encoded as a map, not if/else chains
- DB writes use a single transaction: UPDATE policy status + INSERT audit log row
- `actor_id` comes from the JWT claims (S007 provides this via context)
- Reason code is a controlled vocabulary: `UNDERWRITER_APPROVED`, `UNDERWRITER_REJECTED`, `CUSTOMER_REQUEST`, `NON_PAYMENT`, `REGULATORY`

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes
- [ ] L1: state machine unit tests cover all valid transitions AND all invalid transitions (table-driven tests)
- [ ] PR merged to `staging`
- [ ] DORA Art.9 traceability demonstrated: every transition has actor_id + timestamp + reason

## Tasks

- [ ] TASK-1: Write `internal/domain/state_machine.go` (transition table + Transition function)
- [ ] TASK-2: Write `migrations/V2__audit_log.sql`
- [ ] TASK-3: Write transition endpoints in `internal/api/handlers/transition_handler.go`
- [ ] TASK-4: Write `internal/repository/postgres/audit_log_postgres.go`
- [ ] TASK-5: Write state machine unit tests (table-driven, all transitions)

## Dependencies

- Depends on: S002 (domain model), S003 (service layer)
- Blocks: S006 (events published on transition), REC-POL-01, REC-POL-02
