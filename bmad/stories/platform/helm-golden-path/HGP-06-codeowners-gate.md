---
id: HGP-06
title: "CODEOWNERS + prod gate on values-prod + chart"
status: Done
type: Story
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 2
labels: [platform, gitops, helm, devops]
priority: P2
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Story
Move/extend the prod gate to the Helm surfaces.

## AC
- [x] CODEOWNERS gates services/*/helm/values-prod.yaml, charts/minicloud-app-deployment/**, apps/, manifests/kargo/
- [x] A chart change requires review (all-prod blast radius)
