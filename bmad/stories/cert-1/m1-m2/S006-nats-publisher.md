---
id: S006-nats-publisher
title: "NATS JetStream event publisher — policy lifecycle events"
status: Done
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, nats, events, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **ktayl-claims-service**, I want to receive `policy.created` and `policy.cancelled` events over NATS JetStream so that the claims service can react to policy lifecycle changes without polling the policy API.

## Background

CdCF §8 — event-driven architecture. NATS JetStream is the backbone for inter-service communication. The ktayl-ai-claims-assistant (S006 in M6) also subscribes to `policy.activated` to pre-index documents. CloudEvents 1.0 format ensures consumer-agnostic schema evolution.

## Acceptance Criteria

- [x] AC-1: Events published on every state transition (from S004): `policy.created`, `policy.submitted`, `policy.activated`, `policy.amended`, `policy.cancelled`, `policy.expired`
- [x] AC-2: All events follow CloudEvents 1.0 spec: `specversion`, `id` (UUID), `source` (`ktayl-policy-service`), `type` (`com.ktayl.policy.<event>`), `datacontenttype`, `time`, `data`
- [x] AC-3: JetStream stream `POLICY_EVENTS` created at startup if not exists (subjects: `policy.>`, retention: 7 days, storage: File)
- [x] AC-4: Publisher is transactional — event is only sent AFTER the DB transaction commits (no phantom events)
- [x] AC-5: Failed publishes logged as ERROR + retried up to 3x with exponential backoff (5s, 25s, 125s)
- [x] AC-6: `GET /healthz` includes NATS connection status: `{"nats":"connected"}` or `{"nats":"disconnected"}`

## Technical Notes

- NATS client: `github.com/nats-io/nats.go`
- JetStream publisher pattern: publish after `tx.Commit()` returns nil — outbox pattern not needed at this scale
- For strict at-least-once: use a `policy_outbox` table (insert in same TX, background goroutine drains). Implement outbox if AC-4 proves flaky in load tests.
- CloudEvents Go SDK: `github.com/cloudevents/sdk-go/v2` for envelope construction
- NATS URL from env: `NATS_URL` (default `nats://nats.nats.svc.cluster.local:4222`)
- TLS: use minicloud CA cert injected via `NATS_CA_CERT` env (same pattern as Harbor CA injection)

## Definition of Done

- [x] Code implements all ACs
- [x] L0: golangci-lint passes
- [x] L1: publisher unit tests with `nats-server` embedded test server (`natsserver "github.com/nats-io/nats-server/v2/server"`)
- [x] PR merged to `staging`

## Tasks

- [x] TASK-1: Write `internal/events/publisher.go` (JetStream client + stream setup)
- [x] TASK-2: Write `internal/events/policy_events.go` (CloudEvents envelope per event type)
- [x] TASK-3: Integrate publisher call in `internal/domain/policy_service.go` post-transition
- [x] TASK-4: Add NATS health check to `/healthz`
- [x] TASK-5: Write unit tests with embedded NATS server

## Dependencies

- Depends on: S004 (transitions trigger events)
- Blocks: ktayl-claims-service M3 (subscribes to policy events), ktayl-ai-claims-assistant M6
