---
id: S007-auth-middleware
title: "Authentik M2M JWT middleware — JWKS validation + scope-based authz"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, security, authentik, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **Security Engineer**, I want every API endpoint protected by JWT validation against Authentik so that only authorised services and users can create or modify policies.

## Background

CdCF §7.3 (sécurité) — Authentik is the OIDC/OAuth2 provider. Two token flows are used: (1) M2M client credentials (ktayl-portal BFF → policy-service); (2) user OIDC token forwarded from portal. Scopes enforce least privilege: `policy:read` for GET endpoints, `policy:write` for POST/PUT/DELETE.

## Acceptance Criteria

- [ ] AC-1: All endpoints except `/healthz` require `Authorization: Bearer <token>`; missing token → 401
- [ ] AC-2: Token signature validated against Authentik JWKS (`AUTHENTIK_JWKS_URL` env var); invalid signature → 401
- [ ] AC-3: Token expiry enforced; expired token → 401 with `{"error":"token_expired"}`
- [ ] AC-4: `policy:read` scope required for GET endpoints; missing scope → 403
- [ ] AC-5: `policy:write` scope required for POST/PUT/DELETE; missing scope → 403
- [ ] AC-6: `sub` claim (user or service account ID) stored in request context and used as `actor_id` in audit log (S004 AC-6)
- [ ] AC-7: JWKS keys cached in memory with 5-minute TTL (avoid JWKS lookup on every request)

## Technical Notes

- JWT library: `github.com/golang-jwt/jwt/v5`
- JWKS fetcher: `github.com/MicahParks/keyfunc/v3` (handles RSA + EC, auto-refresh)
- Middleware registered on router in `cmd/server/server.go` — wraps all route groups except `/healthz`
- Scope check: parse `scope` claim (space-separated string) or `scopes` array — Authentik uses space-separated
- For Authentik M2M: create OAuth2 Provider (client credentials) + Application in Authentik; client_id/secret stored in Vault `secret/ktayl/policy-service/authentik`
- Do NOT validate `aud` claim in v1 (Authentik M2M tokens may omit it) — revisit in S-security-hardening

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes
- [ ] L1: middleware unit tests — valid token passes, expired token rejected, missing scope rejected (table-driven, 8 cases)
- [ ] PR merged to `staging`
- [ ] Authentik M2M application configured (manual step, documented in PR description)

## Tasks

- [ ] TASK-1: Write `internal/api/middleware/auth.go` (JWT validation + JWKS cache)
- [ ] TASK-2: Write `internal/api/middleware/authz.go` (scope check per route)
- [ ] TASK-3: Register middleware in router (`cmd/server/server.go`)
- [ ] TASK-4: Write unit tests (mock JWKS server with `httptest`)
- [ ] TASK-5: Create Authentik M2M provider + Vault secret (documented in PR)

## Dependencies

- Depends on: S001 (scaffold), S003 (routes exist to protect)
- Blocks: REC-POL-01 (auth required for acceptance test)
