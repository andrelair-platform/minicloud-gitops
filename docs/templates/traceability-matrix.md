# Traceability Matrix — `<product>`

> **Template.** Copy to `<repo>/docs/traceability-matrix.md` and fill with the product's **real** IDs,
> components, test files and CI stages. A Path-C Definition-of-Done item (`documentation-standard.md`).
> It threads every requirement end-to-end so a change to one requirement shows exactly what else must move.

## Requirement register (stable IDs + an *observable* criterion)

Every requirement gets a stable ID and a **testable** acceptance criterion (not "must be fast").
IDs: `FR-###` functional · `NFR-###` non-functional · `SEC-###` security · `AI-###` AI behaviour.

| ID | Requirement | Acceptance criterion (observable) | Source |
|---|---|---|---|
| FR-001 | <user can do X> | <a valid request triggers Y and returns Z, or an explicit failure> | PRD §<n> |
| SEC-001 | <permission respected> | <an unauthorized caller gets 401/403 and never sees the resource> | PRD §security |
| NFR-001 | <performance> | <p95 < <ms> under <representative load>> | PRD §NFR |
| AI-001 | <grounded answers> | <every claim links a retrievable source on the eval set> | PRD §AI |

## The matrix — requirement → architecture → test → pipeline → evidence

| Requirement ID | Architecture component (C4 / module) | Test (file / case) | Pipeline stage | Evidence |
|---|---|---|---|---|
| FR-001 | `<Component>` | `<path/to/test_x>` | Integration | <link: CI run / report> |
| SEC-001 | `<AuthZ / ACL>` | `<path/to/test_acl>` | Security | <link> |
| NFR-001 | `<Backend / dep>` | `<path/to/load_test>` | Performance | <link: k6 report> |
| AI-001 | `<RAG / Citation>` | `<path/to/eval>` | AI eval | <link: eval run> |

## The question it must answer
> *If `SEC-001` changes tomorrow, which components, tests, pipelines and docs must change?*
Follow the row: the component to edit, the test that must be updated, the pipeline stage that re-gates it,
and the evidence that must be regenerated. Keep the matrix current in the **same PR** as the change.

## Rules
- **IDs are stable and never reused** — a retired requirement's ID is struck through, not recycled.
- **Every requirement has ≥1 test row** — a requirement with no test is untracked, not done.
- **Prefer the real artefact** — link the actual test file + the actual CI job, not a description.
- Keep it in `<repo>/docs/` (committed, reviewed with the code), surfaced on the central map per `documentation.md`.
