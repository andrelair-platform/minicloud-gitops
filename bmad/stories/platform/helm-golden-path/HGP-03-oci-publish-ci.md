---
id: HGP-03
title: "CI: dual-publish the chart OCI — Harbor (dev) + ghcr (prod)"
status: Done
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
Publish minicloud-app-deployment as an OCI Helm chart on version bump, mirroring the image dual-push.

## AC
- [x] CI job: helm package + helm push to oci://harbor.10.0.0.200.nip.io/library and oci://ghcr.io/andrelair-platform on Chart.yaml version change
- [x] SemVer enforced; tag == Chart version
- [x] ghcr package visibility set; Harbor retention applies
- [x] Verify: helm pull from both registries
