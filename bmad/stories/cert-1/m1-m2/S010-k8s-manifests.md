---
id: S010-k8s-manifests
title: "k8s manifests + ArgoCD Application — ktayl-policy-service on cluster"
status: Ready
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

- [ ] AC-1: `kustomize build services/ktayl-policy-service/minicloud-1/dev` exits 0 with no warnings
- [ ] AC-2: ArgoCD Application `ktayl-policy-service` appears in ArgoCD UI under project `minicloud-workloads`, Healthy + Synced after merge to `main`
- [ ] AC-3: `dev` overlay — 1 replica, resource requests CPU 50m/memory 64Mi, image tag updated by CI via `kustomize edit set image`
- [ ] AC-4: `prod` overlay — 2 replicas, resource requests CPU 100m/memory 128Mi, Ingress at `ktayl-policy.10.0.0.200.nip.io` with TLS (minicloud CA cert issuer)
- [ ] AC-5: ExternalSecret pulls PostgreSQL DSN + NATS URL + Authentik JWKS URL from Vault `secret/ktayl/policy-service/` into Secret `ktayl-policy-service-env`
- [ ] AC-6: Liveness probe `GET /healthz` every 10s, startup probe (failureThreshold: 30, periodSeconds: 10 = 5 min budget)
- [ ] AC-7: `ktayl` namespace added to AppProject `minicloud-workloads` destinations
- [ ] AC-8: NetworkPolicy allows ingress from nginx-ingress only; egress to `ktayl-postgres` (5432), NATS (4222), Authentik JWKS (443), MinIO (9000)
- [ ] AC-9: CI job `promote-dev` on push to `main` runs `kustomize edit set image` + commits to `services/ktayl-policy-service/minicloud-1/dev/`

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

- [ ] `kustomize build` passes for all 3 overlays
- [ ] ArgoCD Application Healthy + Synced on cluster after merge
- [ ] `GET https://ktayl-policy.10.0.0.200.nip.io/healthz` returns 200 from Mac (Tailscale + minicloud CA)
- [ ] PR to `minicloud-gitops main` includes ArgoCD Application file and namespace addition to AppProject

## Tasks

- [ ] TASK-1: Create `services/ktayl-policy-service/base/` (kustomization, deployment, service, serviceaccount)
- [ ] TASK-2: Create `services/ktayl-policy-service/minicloud-1/dev/` overlay (image tag placeholder, HPA off)
- [ ] TASK-3: Create `services/ktayl-policy-service/minicloud-1/staging/` overlay
- [ ] TASK-4: Create `services/ktayl-policy-service/minicloud-1/prod/` overlay (ingress, cert, 2 replicas)
- [ ] TASK-5: Write `manifests/ktayl/00-namespace.yaml` + `01-postgres.yaml` + `02-network-policies.yaml` + `03-externalsecret.yaml`
- [ ] TASK-6: Write `apps/workloads/ktayl-policy-service.yaml` ArgoCD Application
- [ ] TASK-7: Edit `manifests/argocd-project/00-project.yaml` — add `ktayl` ns to destinations
- [ ] TASK-8: Add `promote-dev` CI job to `.github/workflows/ci.yml` in `ktayl-policy-service` repo
- [ ] TASK-9: Add `catalog-info.yaml` to service repo (Backstage entity, type=service, system=ktayl)

## Dependencies

- Depends on: S001 (image exists in Harbor), S003 (healthz endpoint), S007 (env vars needed)
- Blocks: REC-POL-01 (E2E smoke test needs running service on cluster)
