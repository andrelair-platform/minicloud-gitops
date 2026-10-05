# Case Study — <title>

> Copy to `docs/evidence/case-studies/<slug>.md`. The architect's dossier for one workstream. Steps
> **#3 Options** and **#4 Trade-offs** are mandatory — they are the problem-solver signal. Link, don't
> duplicate: point to the ADR for the decision and the Game Day/postmortem for the failure proof.

## 1. Business problem
_The real driver (an incident, a gap, a constraint) — not "I wanted to learn X"._

## 2. Constraints
_Scale · consistency · auditability · downtime tolerance · cost/footprint · regulation._

## 3. Options considered
_2–3 real alternatives (A / B / C)._

## 4. Trade-offs
_Why each option wins/loses against the constraints. The crux._

## 5. Decision
_What you chose + why. → link the ADR._

## 6. Implementation
_The shape: resources / data model / flow. Where state lives, where secrets live, the boundaries._

## 7. Failure behaviour
_What happens when a dependency dies; how it rolls back. → link the Game Day / postmortem._

## 8. Measurement
_The numbers: p95 latency · throughput · error rate · MTTR · RPO/RTO · coverage · €/request._
_Every claim backed by a graph/log/metric — "it works" is not evidence._

## 9. Lesson learned
_What you'd do differently; what transferred to the next problem._

---
**Proof-catalog row:** add/update the matching line in `docs/evidence/proof-catalog.md`.
**System-design pattern(s) used:** append to `docs/evidence/system-design-patterns.md` if novel.
**Publish:** a problem-framed LinkedIn/portfolio post when it's strong.
