---
id: HGP-07
title: "platform-demo pilot cutover + verify"
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
Cut platform-demo fully onto the Helm golden path, prove end-to-end, retire its kustomize overlays.

## AC
- [ ] dev+prod on the shared chart; KEDA scale-to-zero works; ingress+TLS + demo.devandre.sbs live
- [ ] Kargo dev auto-promote + prod PR verified; canary/health brake intact
- [ ] Old services/platform-demo kustomize overlays removed after verification
- [ ] Rollback path proven (repoint App to overlay)
