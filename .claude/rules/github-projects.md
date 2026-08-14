# GitHub Projects — Issue Tracking Rules

## The board

**Project:** `andrelair-platform` — minicloud platform roadmap
**URL:** https://github.com/orgs/andrelair-platform/projects/1

## Tier views (always use these for context)

| Tier | View | Filter |
|---|---|---|
| **Tier 1 — P1-blocking** (22 issues, actively owned) | https://github.com/orgs/andrelair-platform/projects/1/views/11?filterQuery=label%3AP1-blocking | Your weekly review list |
| **Tier 2 — Steady state** (127 issues, exception-only) | https://github.com/orgs/andrelair-platform/projects/1/views/12?filterQuery=label%3AP2-high-value | Monitor on Amber/Red only |
| **Tier 3 — Icebox** (28 issues, parked) | https://github.com/orgs/andrelair-platform/projects/1/views/13?filterQuery=label%3AP5-supplemental | Ignore until unfrozen |

## Mandatory rules when working on any issue

### 1. Link every PR to its issue

When opening a PR that implements or partially implements a `platform-backlog` issue, always include the link in the PR body:

```
Closes andrelair-platform/platform-backlog#<NUMBER>
```

or for partial work:

```
Relates to andrelair-platform/platform-backlog#<NUMBER>
```

GitHub Projects picks up the linked PR automatically and shows it in the "Linked pull requests" column.

### 2. Create sub-issues for large issues

If an issue in the board is too large to close in a single PR (epics, multi-week work), break it into sub-issues:

```bash
# Create a sub-issue linked to the parent
gh issue create \
  --repo andrelair-platform/platform-backlog \
  --title "[S001-slug] Sub-task title" \
  --label "<same labels as parent>" \
  --body "Parent: andrelair-platform/platform-backlog#<PARENT_NUMBER>\n\n..."
```

Then on the parent issue, use GitHub's native sub-issues feature (available in Projects v2) — the "Sub-issues progress" field on the board will auto-populate.

### 3. Update issue status on the board as you work

Use the project `Status` field — update it as work progresses:

```bash
# Get the project item ID for an issue
gh api graphql -f query='
{
  node(id: "PVT_kwDOEN4i9s4BbQIF") {
    ... on ProjectV2 {
      items(first: 100) {
        nodes {
          id
          content { ... on Issue { number } }
        }
      }
    }
  }
}'

# Update status (Status field ID: PVTSSF_lADOEN4i9s4BbQIFzhWB8R4)
# Status option IDs:
#   Backlog      → 3ac5aad0
#   This Sprint  → 26e76715
#   In Progress  → d4b08afe
#   Blocked      → 9ab1df6d
#   In Review    → b6090f99
#   Done         → 99316423
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwDOEN4i9s4BbQIF"
    itemId: "<ITEM_ID>"
    fieldId: "PVTSSF_lADOEN4i9s4BbQIFzhWB8R4"
    value: { singleSelectOptionId: "d4b08afe" }
  }) { projectV2Item { id } }
}'
```

### 4. Set Priority field when promoting an issue to active work

The board has a native `Priority` field (separate from labels) — set it when moving an issue to "This Sprint" or "In Progress":

| Board Priority | Label equivalent |
|---|---|
| P1 — Critical | `P1-blocking` |
| P2 — High | `P2-high-value` |
| P3 — Medium | `P4-platform-polish` |
| P4 — Low | — |
| P5 — Deferred | `P5-supplemental` |

### 5. Always work Tier 1 before opening new issues

Before creating new issues or starting Tier 2 work, check the Tier 1 view:
https://github.com/orgs/andrelair-platform/projects/1/views/11?filterQuery=label%3AP1-blocking

If any Tier 1 issue is `In Progress` or `Blocked`, resolve it first.

## Project field IDs (for GraphQL mutations)

| Field | ID |
|---|---|
| Status | `PVTSSF_lADOEN4i9s4BbQIFzhWB8R4` |
| Priority | `PVTSSF_lADOEN4i9s4BbQIFzhWB9gE` |
| Domain | `PVTSSF_lADOEN4i9s4BbQIFzhXy6tY` |
| Effort | `PVTSSF_lADOEN4i9s4BbQIFzhXy6v4` |
| Sprint | `PVTIF_lADOEN4i9s4BbQIFzhXy__c` |
| Track | `PVTSSF_lADOEN4i9s4BbQIFzhaH6GY` |
| Kind | `PVTSSF_lADOEN4i9s4BbQIFzhaLrh8` |
| Start Date | `PVTF_lADOEN4i9s4BbQIFzhaLriA` |
| Project node ID | `PVT_kwDOEN4i9s4BbQIF` |
