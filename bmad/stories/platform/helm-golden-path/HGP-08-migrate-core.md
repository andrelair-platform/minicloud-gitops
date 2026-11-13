---
id: HGP-08
title: "Migrate plane, agent, crew, ktayl-policy to the golden path"
status: Done
type: Story
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 13
labels: [platform, gitops, helm, devops]
priority: P2
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Story
Convert the remaining single/standard services (one at a time) to values-only on the shared chart.

## AC
- [x] minicloud-plane (Rollout mode), minicloud-agent + minicloud-crew-agent (ghcr-pull + ESO), ktayl-policy-service
- [x] each verified dev→prod, kustomize overlays retired, rollback proven
