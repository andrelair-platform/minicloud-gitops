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
3. **Definition of Done** — a story closes only when it meets DoD: code written, reviewed, **tested (testing.md L0–L4)**, and deployed to `dev` (promotable to prod via the Kargo/CODEOWNERS-gated PR). No story is "Done" on code alone.
4. **Sprint Review (demo)** — demonstrate the working increment.
5. **Retrospective** — reflect on what to improve. Use `/bmad-review`.

## 3. Mapping onto the GitHub Projects (portfolio of products)

The hierarchy maps onto the **product boards** — one Project per product — with **#1 as the
cross-product roll-up** (see `github-projects.md`). Use these fields; don't invent parallel tracking.
The **Initiative** (Insurance LOB · Certification · IS Foundations) is a **grouping field on the
roll-up**, not a board.

| Scrum layer | Where it lives | Field / view |
|---|---|---|
| Initiative / Theme | Insurance LOB · Certification · IS Foundations | a **grouping field** on the #1 roll-up (Initiative → Product); never a board |
| **Product** | one **GitHub Project (v2) per product** (1..N repos, own backlog) | the product board itself |
| **Epic** | GitHub issue with **`Kind=Epic`** + its **Milestone**, on the product board | Milestone ≈ the epic's home / time-span |
| **User Story** | `S###` / `RTV-##` issue, **`Kind=Story`**, body in user-voice, on the product board | authored via per-product BMAD (`bmad.md`) |
| **Task** | checklist item / sub-issue inside a story | sized by **`Effort`** (XS→XL) |
| **Sprint** | 2-week iteration | **`Sprint`** field (per product board) |
| **Product Backlog** | each product board's open list | the board's `Backlog` view (#1 = union / PMO view only) |

**Status flow** mirrors Scrum exactly: `Backlog → This Sprint → In Progress → Blocked → In Review → Done`.

**Assigning a story to a sprint = setting the `Sprint` iteration field** (not only `Status="This Sprint"`). The "Current Sprint" / "Sprint Board" views filter on `sprint:@current` — a story missing the iteration value will not appear there.

### Two conventions to keep the hierarchy explicit

1. **`Kind=Story`** — every `S###`/`RTV-##` gets `Kind=Story` under its `Kind=Epic` parent. (If the option is missing from the field, add it: Settings → Fields → Kind → add "Story".)
2. **User-voice bodies** — the story body leads with the *As a [role], I want [x] so that [benefit]* block (already in `bmad/templates/story-template.md`). The issue title may stay `[S001-slug] …`; the value statement lives in the body.

## 4. BMAD = the tooling for each ceremony

BMAD is not a separate process — it is how each Scrum event is executed. Pipeline: author a story `.md` in the **product home repo** → merge to that repo's main → its thin caller `.github/workflows/bmad-sync.yml` (which `uses:` the org-shared reusable workflow) creates the GitHub Issue in the concerned repo + on the product board → box it into the current Sprint → build → review. (See `bmad.md` *Per-product BMAD*.)

| Ceremony / layer | BMAD tool | Output |
|---|---|---|
| Backlog refinement / write **stories** | `/bmad-agent-mary` (BA) + `/bmad-agent-john` (PM) | `<home-repo>/bmad/stories/<sprint>/S###.md` |
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
