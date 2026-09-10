---
id: HGP-01
title: "EPIC: Helm library-chart golden path for custom apps"
status: Ready
type: Epic
epic: helm-golden-path
milestone: "HGP — Helm golden path"
estimate: 21
labels: [platform, gitops, helm, devops]
priority: P1
assignee: AndreLiar
repo: andrelair-platform/minicloud-gitops
project: 3
---

## Epic
Replace Kustomize-for-custom with one shared Helm chart (**minicloud-app-deployment**) + thin per-app values, published OCI dev=Harbor/prod=ghcr, consumed by ArgoCD multi-source. One tool, one golden path; third-party charts unchanged. See ADR docs/helm-golden-path.md.

## Stories
HGP-02 library chart · HGP-03 OCI publish CI · HGP-04 ArgoCD multi-source · HGP-05 Kargo yaml-update · HGP-06 CODEOWNERS gate · HGP-07 platform-demo pilot · HGP-08 migrate plane/agent/crew/policy · HGP-09 migrate retrieva.

## Done when
All 6 custom services run off the shared chart on dev+prod; kustomize overlays retired.
