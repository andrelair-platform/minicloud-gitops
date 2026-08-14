---
id: intro
title: Overview
sidebar_label: Overview
slug: /
---

# minicloud GitOps

**Single source of truth** for the minicloud platform — ArgoCD continuously reconciles the cluster against this repository. All Helm values, Kustomize overlays, network policies, RBAC, Gatekeeper constraints, and BMAD sprint stories live here.

## Responsibility

| In scope | Out of scope |
|---|---|
| ArgoCD app-of-apps (43 platform + 28 workload apps) | Bare-metal provisioning (minicloud-opentofu) |
| All Helm values (`helm-values/minicloud-1/`) | Node bootstrap (minicloud-ansible) |
| Kustomize overlays for all custom services | Application source code (per-service repos) |
| Network policies, RBAC, Gatekeeper constraints | |
| BMAD sprint stories (`bmad/stories/`) | |
| Claude Code context rules (`.claude/rules/`) | |

## Stack

| Concern | Choice |
|---|---|
| GitOps engine | ArgoCD 2.14.x |
| Helm | 3.x — values in `helm-values/minicloud-1/` |
| Kustomize | 5.6.x — overlays in `services/*/minicloud-1/` |
| Cluster | k3s (kubectl context: `minicloud`) |
| Secrets | External Secrets Operator + Vault |

## Repository layout

```
apps/
  platform/        # 43 platform ArgoCD Applications
  workloads/       # 28 service ArgoCD Applications
helm-values/
  minicloud-1/     # All Helm values keyed by chart name
services/
  <service>/
    base/          # No namespace, no image tag
    minicloud-1/
      dev/         # CI bumps image tag here
      staging/     # Promoted via PR
      prod/        # Promoted via PR + ingress
manifests/         # Raw k8s manifests (Longhorn, ArgoCD project, NetworkPolicies…)
bmad/
  stories/         # BMAD sprint stories → synced to GitHub Issues via bmad-sync.yml
.claude/rules/     # Claude Code context files (public rules only)
```

## Promotion flow

```
CI push → dev overlay (auto) → PR to staging → PR to main (prod)
```

## Links

- [GitHub repository](https://github.com/andrelair-platform/minicloud-gitops)
- [ArgoCD](https://argocd.devandre.sbs)
- [Platform documentation](https://andrelair-platform.github.io/minicloud-platform-docs/)
