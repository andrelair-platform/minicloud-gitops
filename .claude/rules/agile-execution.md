# Agile / Scrum Execution Standard

All work on the platform follows one nested work hierarchy delivered through fixed 2-week Sprints. This is the mandatory execution model — every task, story, and epic maps into it, and BMAD is the tooling for each ceremony. Companion files: `bmad.md` (workflow), `bmad-compliance.md` (per-repo tracker), `github-projects.md` (board field IDs), `testing.md` (Definition of Done).

## 1. The work hierarchy

```
[ Initiative / Theme ]   broad strategy (multi-quarter)
        │
     [ Epic ]            large body of work (several sprints, 1–3 months)
        │
  [ User Story ]         deliverable unit of value (fits in ONE sprint)
        │
     [ Task ]            technical to-do (hours → 1–2 days)
```

- **Initiative / Theme** — the highest strategic layer. On this platform the three themes are **Insurance LOB**, **Certification (Retrieva / RNCP39583)**, and **IS Foundations**.
- **Epic** — a major feature/milestone that cannot ship in one sprint (e.g. "ktayl-policy-service", "Retrieva DORA compliance"). Broken into multiple user stories.
- **User Story** — a functional unit of value written from the user's perspective:
  > *As a [role], I want [action] so that [benefit].*
  A story MUST fit inside a single sprint. If it can't, it's an epic — split it.
- **Task / Sub-task** — the technical steps to complete a story (e.g. "integrate Flyway migration", "write unit tests for premium calc").

## 2. The execution loop (the Sprint)

Sprints are **fixed 2-week iterations** (the `Sprint` field on project #1).

```
Product Backlog ─(Sprint Planning)→ Sprint Backlog ─(Daily / Build)→ Increment ─(Review + Retrospective)
```

1. **Sprint Planning** — prioritized stories move from the Product Backlog into the Sprint Backlog based on velocity. Gate with `/bmad-sprint-planning` (PASS/CONCERNS/FAIL) before coding.
2. **Execution & Daily** — build the committed stories; surface progress/blockers.
3. **Definition of Done** — a story closes only when it meets DoD: code written, reviewed, **tested (testing.md L0–L4)**, and deployed to staging. No story is "Done" on code alone.
4. **Sprint Review (demo)** — demonstrate the working increment.
5. **Retrospective** — reflect on what to improve. Use `/bmad-review`.

## 3. Mapping onto GitHub Project #1

`andrelair-platform` project #1 already carries the whole hierarchy in its fields — use them, don't invent parallel tracking.

| Scrum layer | Project artifact | Field / view |
|---|---|---|
| Initiative / Theme | Insurance LOB · Certification · IS Foundations | (Milestone naming; `Track` field) |
| **Epic** | GitHub issue with **`Kind=Epic`** + its **Milestone** | Milestone ≈ the epic's home / time-span |
| **User Story** | `S###` / `RTV-##` issue, **`Kind=Story`**, body in user-voice | see gap below |
| **Task** | checklist item / sub-issue inside a story | sized by **`Effort`** (XS→XL) |
| **Sprint** | 2-week iteration | **`Sprint`** field |
| **Product Backlog** | the master open list | **`Backlog`** view |

**Status flow** mirrors Scrum exactly: `Backlog → This Sprint → In Progress → Blocked → In Review → Done`.

**Assigning a story to a sprint = setting the `Sprint` iteration field** (not only `Status="This Sprint"`). The "Current Sprint" / "Sprint Board" views filter on `sprint:@current` — a story missing the iteration value will not appear there.

### Two conventions to keep the hierarchy explicit

1. **`Kind=Story`** — every `S###`/`RTV-##` gets `Kind=Story` under its `Kind=Epic` parent. (If the option is missing from the field, add it: Settings → Fields → Kind → add "Story".)
2. **User-voice bodies** — the story body leads with the *As a [role], I want [x] so that [benefit]* block (already in `bmad/templates/story-template.md`). The issue title may stay `[S001-slug] …`; the value statement lives in the body.

## 4. BMAD = the tooling for each ceremony

BMAD is not a separate process — it is how each Scrum event is executed. Pipeline: author a story `.md` → merge to gitops main → `.github/workflows/bmad-sync.yml` auto-creates the GitHub Issue on its milestone → box it into the current Sprint → build → review.

| Ceremony / layer | BMAD tool | Output |
|---|---|---|
| Backlog refinement / write **stories** | `/bmad-agent-mary` (BA) + `/bmad-agent-john` (PM) | `bmad/stories/<proj>/<milestone>/S###.md` |
| Epic **architecture** | `/bmad-agent-winston` + `/bmad-party-mode` | ADRs / architecture doc |
| **Sprint Planning** (readiness gate) | `/bmad-sprint-planning` | PASS/CONCERNS/FAIL + `sprint-status.yaml` |
| **Execution** (build) | `/bmad-build` (one story) · `/bmad-build-auto` (multi, autonomous) | code + tests, DoD-checked |
| **Definition of Done** | `testing.md` L0–L4 gates + story ACs | passing CI |
| **Review + Retrospective** | `/bmad-review` (via agent) | evidence-based retro |

## 5. Quick reference

| Concept | Scope | Time horizon | Owner |
|---|---|---|---|
| **Epic** | major functional area | 1–3 months (multi-sprint) | Product Owner |
| **User Story** | specific user-facing value | within one sprint | PO & Developers |
| **Task** | granular implementation | hours → 1–2 days | individual dev |
| **Sprint** | fixed cadence container | 2 weeks (fixed) | whole team |
| **Product Backlog** | master wishlist | living document | Product Owner |
