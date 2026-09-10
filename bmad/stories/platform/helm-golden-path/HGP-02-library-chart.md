---
id: HGP-02
title: "minicloud-app-deployment library chart (Deployment/Rollout + core resources)"
status: In Progress
type: Story
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 8
labels: [platform, gitops, helm, devops]
priority: P1
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Story
As a platform engineer, I want one hardened, versioned Helm chart rendering the full app resource set from values, so every custom app is a thin values file.

## AC
- [x] Chart renders Deployment OR Argo Rollout (canary/blueGreen)
- [x] Service, Ingress+Certificate, KEDA ScaledObject|HPA, egress NetworkPolicy, PDB, ServiceMonitor, ESO ExternalSecret — all value-toggled
- [x] Secure defaults: runAsNonRoot, readOnlyRootFS, seccomp, drop ALL, limits mandatory; writableDirs emptyDir
- [x] helm lint + helm template validated (dev 5 resources, prod 7)

**Delivered in the initial PR (charts/minicloud-app-deployment/).**
