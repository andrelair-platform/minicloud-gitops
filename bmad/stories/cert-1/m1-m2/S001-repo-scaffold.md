---
id: S001-repo-scaffold
title: "ktayl-policy-service — Go module scaffold, Makefile, CI skeleton"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 2
labels: [go, ci-cd, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As a **Tech Lead**, I want a production-ready Go repository scaffold so that all subsequent stories build on a consistent, lintable, testable base from day one.

## Background

ktayl-policy-service is the first microservice of the ktayl-solution IS (CdCF §4, issue #203). It must follow the org-wide CI/registry standard (`.claude/rules/ci-registry.md`): Harbor push via Tailscale, golangci-lint, go test, cosign on staging/main.

## Acceptance Criteria

- [ ] AC-1: `go build ./...` succeeds with Go 1.23, zero warnings
- [ ] AC-2: `make lint` runs golangci-lint with project `.golangci.yml` (errcheck, staticcheck, govet, unused)
- [ ] AC-3: `make test` runs `go test ./... -race -count=1` and exits 0
- [ ] AC-4: `make build` produces a statically-linked Linux/amd64 binary via multi-stage Containerfile
- [ ] AC-5: GitHub Actions CI triggers on push to `dev` — lint + test + Harbor push of `dev-<sha>` image
- [ ] AC-6: `catalog-info.yaml` registered with Backstage (kind: Component, type: service)

## Technical Notes

- Use `cmd/server/main.go` entry point pattern (same as minicloud-plane)
- Internal packages: `internal/api`, `internal/domain`, `internal/repository`, `internal/events`
- Config via `github.com/spf13/viper` (env vars + YAML fallback)
- HTTP server: `github.com/go-chi/chi/v5`
- Structured logging: `log/slog` (stdlib, Go 1.21+)
- Containerfile: `FROM golang:1.23-alpine AS builder` → `FROM gcr.io/distroless/static:nonroot`
- CA cert injection at build time: `ARG CA_CERT` (org-wide pattern, never committed)

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes (0 errors)
- [ ] L1: smoke test in `main_test.go` (server starts, `/healthz` returns 200)
- [ ] PR merged to `staging`
- [ ] ArgoCD: n/a (no k8s manifests yet — S010)

## Tasks

- [ ] TASK-1: `gh repo create andrelair-platform/ktayl-policy-service --public`
- [ ] TASK-2: `go mod init github.com/andrelair-platform/ktayl-policy-service`
- [ ] TASK-3: Create directory layout (`cmd/`, `internal/`, `k6/`)
- [ ] TASK-4: Write `.golangci.yml`, `Makefile`, `.gitignore`
- [ ] TASK-5: Write multi-stage `Containerfile`
- [ ] TASK-6: Copy CI workflow from `minicloud-plane/.github/workflows/ci.yml`, update image name
- [ ] TASK-7: Write `catalog-info.yaml`
- [ ] TASK-8: Open PR `dev` → merge

## Dependencies

- Depends on: none (first story)
- Blocks: S002, S003, S004, S005, S006, S007, S008, S009, S010
