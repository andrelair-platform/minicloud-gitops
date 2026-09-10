---
id: HGP-04
title: "ArgoCD multi-source pattern (OCI chart + git values) for platform-demo"
status: Ready
type: Story
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 5
labels: [platform, gitops, helm, devops]
priority: P1
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Story
Wire dev/prod ArgoCD Applications that combine the OCI chart with git-hosted values.

## AC
- [ ] platform-demo-dev App: source1 oci Harbor chart + source2 gitops values.yaml+values-dev.yaml (\$values)
- [ ] platform-demo-prod App: source1 oci ghcr chart + source2 values.yaml+values-prod.yaml
- [ ] ESO ignoreDifferences carried over; auto-sync (prod git-gated)
- [ ] Both render Synced/Healthy against the OCI chart
