---
id: HGP-09
title: "Migrate retrieva to the golden path (2 images, git Warehouse)"
status: Done
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
- [x] retrieva-dev/prod on the shared chart (two workloads or two releases)
- [x] git-Warehouse promotion adapted to values; runtime __ENV__ preserved
- [x] verified dev→prod; overlays retired
