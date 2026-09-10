---
id: HGP-05
title: "Kargo: promote via yaml-update on values files"
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
Change Kargo promotion image-bump from kustomize-set-image to a yaml-update on the values files.

## AC
- [ ] dev/prod Stage promotionTemplate sets .image.tag in values-dev.yaml / values-prod.yaml
- [ ] dev auto-promote + prod CODEOWNERS PR + squash unchanged
- [ ] Verified on platform-demo freight
