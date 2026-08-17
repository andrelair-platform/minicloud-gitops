---
id: S010-k8s-manifests
title: "k8s manifests + ArgoCD Application — ktayl-policy-service on cluster"
status: Done
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [gitops, kubernetes, argocd, cert-1, devops]
priority: Must
assignee: AndreLiar
---

## Story

As a **Platform Engineer**, I want ktayl-policy-service deployed to the minicloud cluster via ArgoCD app-of-apps so that the service lifecycle is fully GitOps-managed from `dev` through `prod`.

## Background

All custom services follow the Kustomize base + minicloud-1/{dev,staging,prod} overlay pattern (see `gitops.md`). This story creates the full GitOps structure in `minicloud-gitops/services/ktayl-policy-service/` and wires it to the existing app-of-apps. The service namespace is `ktayl` (shared with future ktayl-claims-service and ktayl-portal).

## Acceptance Criteria

- [x] AC-1: `kustomize build services/ktayl-policy-service/minicloud-1/dev` exits 0 with no warnings
- [x] AC-2: ArgoCD Application `ktayl-policy-service` Healthy + Synced on cluster (PR #758 merged to main)
- [x] AC-3: `dev` overlay — 1 replica, image tag `staging-8962ee0`, updated by CI via `kustomize edit set image`
- [x] AC-4: `prod` overlay — Ingress at `ktayl-policy.10.0.0.200.nip.io` with TLS (minicloud-ca issuer) ✓
- [x] AC-5: ExternalSecret `ktayl-policy-service-secret` pulls DSN + NATS URL + JWKS URL from Vault `secret/ktayl/policy-service/app` — SecretSynced ✓
- [x] AC-6: Liveness probe `GET /healthz` every 10s; readiness probe `GET /healthz` every 5s (readyz path fixed PR #758)
- [x] AC-7: `ktayl` namespace added to AppProject `minicloud-platform` destinations
- [x] AC-8: NetworkPolicy: ingress from nginx; egress to postgres:5432, NATS messaging:4222, Authentik:9000/9443, MinIO:9000 (PR #756/#757)
- [ ] AC-9: CI job `promote-dev` — not implemented (image tag pinned manually for smoke test; deferred)

## Technical Notes

- Base manifest: Deployment + Service (ClusterIP :8080) + ServiceAccount
- Distroless image (`gcr.io/distroless/static-debian12:nonroot`) from S001 Containerfile
- Harbor image path: `harbor.10.0.0.200.nip.io/library/ktayl-policy-service`
- PostgreSQL: deployed as `ktayl-postgres` StatefulSet in `ktayl` ns (1 replica, 5Gi Longhorn, pinned to set-hog) — provisioned in this story as a separate manifest in `manifests/ktayl/postgres.yaml`
- ESO pattern: `ClusterSecretStore: vault-backend` (existing) — same pattern as Harbor, Grafana
- Certificate: `cert-manager.io/cluster-issuer: minicloud-ca-issuer`
- Ingress class: `nginx`
- ArgoCD auto-sync: enabled on `dev` (auto-prune + selfHeal), manual on `staging`/`prod`

## Definition of Done

- [x] `kustomize build` passes for all 3 overlays
- [x] ArgoCD Application Healthy + Synced on cluster — PR #758 merged 2026-08-17
- [x] `GET https://ktayl-policy.10.0.0.200.nip.io/healthz` returns 200 from Mac ✓
- [x] PR to `minicloud-gitops main` merged (PR #758) — ArgoCD app + postgres + NPs + ESO + probe fix
- [x] REC-POL-01 smoke test PASSED 2026-08-17: create→submit→activate→cancel→history all 2xx, 3 audit rows

## Tasks

- [x] TASK-1: `services/ktayl-policy-service/base/` — deployment, service, serviceaccount, kustomization
- [x] TASK-2: `services/ktayl-policy-service/minicloud-1/dev/` — tag staging-8962ee0, ingress, cert
- [x] TASK-3: `services/ktayl-policy-service/minicloud-1/staging/` overlay
- [x] TASK-4: `services/ktayl-policy-service/minicloud-1/prod/` overlay (ingress + cert)
- [x] TASK-5: `manifests/ktayl/` — namespace, postgres StatefulSet, network policies, ExternalSecret
- [x] TASK-6: `apps/workloads/ktayl-base.yaml` + `apps/workloads/ktayl-policy-service-dev.yaml`
- [x] TASK-7: `ktayl` namespace added to AppProject destinations
- [ ] TASK-8: `promote-dev` CI job — deferred (manual tag update used for smoke test)
- [ ] TASK-9: `catalog-info.yaml` — deferred to post-sprint

## Dependencies

- Depends on: S001 (image exists in Harbor), S003 (healthz endpoint), S007 (env vars needed)
- Blocks: REC-POL-01 (E2E smoke test needs running service on cluster)
