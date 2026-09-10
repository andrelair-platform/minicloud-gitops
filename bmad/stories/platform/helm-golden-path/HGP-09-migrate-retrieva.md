---
id: HGP-09
title: "Migrate retrieva to the golden path (2 images, git Warehouse)"
status: Ready
type: Story
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 8
labels: [platform, gitops, helm, devops]
priority: P2
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Story
Convert retrieva last — most complex (backend+frontend images, git Warehouse, runtime-config frontend).

## AC
- [ ] retrieva-dev/prod on the shared chart (two workloads or two releases)
- [ ] git-Warehouse promotion adapted to values; runtime __ENV__ preserved
- [ ] verified dev→prod; overlays retired
