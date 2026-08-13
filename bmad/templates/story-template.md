---
id: SXXX-short-slug
title: "Story title"
status: Draft
type: Story
epic: epic-slug
milestone: "CERT-1 MX — description"
estimate: 3
labels: [backend, cert-1]
priority: Must
assignee: AndreLiar
---

## Story

As a **{role}**, I want **{action}** so that **{benefit}**.

## Background

{context from CdCF or architecture doc}

## Acceptance Criteria

- [ ] AC-1:
- [ ] AC-2:
- [ ] AC-3:

## Technical Notes

{implementation guidance — patterns, constraints, gotchas}

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint / ruff / eslint passes (0 errors)
- [ ] L1: unit tests written, coverage ≥ 70% on new code
- [ ] OpenAPI spec updated if endpoint added
- [ ] PR merged to `staging`
- [ ] ArgoCD: Synced + Healthy in dev environment

## Tasks

- [ ] TASK-1:
- [ ] TASK-2:
- [ ] TASK-3:

## Dependencies

- Depends on: none
- Blocks: none
