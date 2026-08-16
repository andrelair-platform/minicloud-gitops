# CERT-1 M1-M2 — ktayl-policy-service (Go)

**Milestone:** CERT-1 M1-M2 — ktayl-policy-service (Go)
**Sprint start:** 2026-08-13
**Sprint target:** 2026-09-14 (4 weeks)
**Total SP:** 30
**Tech lead:** AndreLiar
**Repo:** https://github.com/andrelair-platform/ktayl-policy-service
**Board:** https://github.com/orgs/andrelair-platform/projects/1
**GitHub milestone:** https://github.com/andrelair-platform/platform-backlog/milestone/11

---

## Sprint Goal

Deliver a fully operational policy lifecycle microservice in Go — REST API, state machine, document
generation, NATS event publishing, JWT auth — deployed on minicloud via ArgoCD. Sprint gate: **REC-POL-01**
(full create → activate → attestation PDF → cancel flow reachable from Mac via HTTPS).

---

## Story Tracker

| ID | Title | SP | Status | Issue | PR |
|---|---|---|---|---|---|
| S001 | Repo scaffold + CI skeleton | 2 | ✅ Done | #250 | #1–#11 |
| S002 | Domain model + PostgreSQL schema | 3 | ✅ Done | #251 | merged |
| S003 | Policy REST API — CRUD + OpenAPI | 5 | ✅ Done | #252 | feat/s003 |
| S004 | State machine + DORA audit log | 3 | ✅ Done | #253 | PR #16 |
| S007 | Auth middleware — Authentik JWKS | 3 | ✅ Done | #256 | feat/s007 |
| S005 | PDF attestation + MinIO storage | 3 | ✅ Done | #254 | PR #17 |
| S006 | NATS JetStream event publisher | 3 | ✅ Done | #255 | PR #18 |
| S008 | Unit test suite + golangci-lint CI | 2 | ✅ Done | #257 | PR #19 |
| S009 | Integration tests (Docker Compose) | 3 | ✅ Done | #258 | PR #20 |
| S010 | k8s manifests + ArgoCD Application | 3 | 🔵 Ready | #259 | — |

**Progress:** 27 / 30 SP done (90%)

---

## Dependency Graph

```
S001 ✅ → S002 ✅ → S003 → S004 → S006
                  ↓         ↓
                 S007      S005
                  ↓
              S008 / S009
                  ↓
                S010
```

S003 blocks everything. S007 and S005 can be developed in parallel after S003 merges.
S009 requires S003–S007 all merged to staging.

---

## PR Strategy

| PR | Branch (ktayl-policy-service) | Target | Closes |
|---|---|---|---|
| PR-A | feat/s003-policy-crud-api | staging | #250, #252 |
| PR-B | feat/s004-state-machine | staging | #253 |
| PR-C | feat/s007-auth-middleware | staging | #256 |
| PR-D | feat/s005-document-gen | staging | #254 |
| PR-E | feat/s006-nats-publisher | staging | #255 |
| PR-F | feat/s008-unit-tests | staging | #257 |
| PR-G | feat/s009-integration-tests | staging | #258 |
| PR-H | sprint-close | main | — |
| PR-I | feat/s010-k8s-manifests (minicloud-gitops) | main | #259 |

---

## Sprint Gate — REC-POL-01

Full policy lifecycle callable from Mac (Tailscale + minicloud CA):

```
POST /v1/policies           → 201, id returned
POST /v1/policies/:id/submit   → 200, status=submitted
POST /v1/policies/:id/activate → 200, status=active
POST /v1/policies/:id/documents/attestation → 200, {url, expires_at}
POST /v1/policies/:id/cancel   → 200, status=cancelled
GET  /v1/policies/:id/history  → 200, 4 audit rows
```

Target URL: `https://ktayl-policy.10.0.0.200.nip.io`

---

## New Go Dependencies (to add before S003)

```
github.com/go-playground/validator/v10    # request validation
github.com/golang-jwt/jwt/v5             # S007
github.com/MicahParks/keyfunc/v3         # JWKS cache S007
github.com/nats-io/nats.go               # S006
github.com/cloudevents/sdk-go/v2         # S006
github.com/minio/minio-go/v7             # S005
github.com/go-pdf/fpdf                   # S005 (no CGO)
github.com/nats-io/nats-server/v2        # unit test embedded NATS
github.com/testcontainers/testcontainers-go  # S009 L2 tests
```

---

## Architecture Decisions

- **PostgreSQL**: dedicated `ktayl-postgres` StatefulSet in `ktayl` ns, pinned to set-hog. 5Gi Longhorn RWO.
- **Auth**: Authentik M2M client credentials for service-to-service; user OIDC for portal consumers.
- **Events**: publish after `tx.Commit()` (goroutine); outbox pattern deferred until load tests prove it needed.
- **PDF**: `go-pdf/fpdf` (no CGO — distroless image compatible).
- **MinIO bucket**: `policy-documents`, 7-year lifecycle (ACPR Art.L113-5).

---

## Implementation Notes

See `IMPL-NOTES.md` in this directory for detailed file-by-file implementation guide.
