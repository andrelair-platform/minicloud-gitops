# Evidence & Proof — turn work into interview-grade proofs (not a tech list)

The goal of this platform is **not** "I learned 50 technologies." It's **"I have 30–50 proofs that I can
solve real engineering problems."** A recruiter is unmoved by *"I have 40 tools in my cluster"*; they lean
in at *"I designed a system, set its SLOs, automated its delivery, induced failures, recovered from DR,
integrated a legacy SOAP core, and here is the evidence."* This rule makes every substantial workstream
leave **three interview artifacts**: a **case study**, a **proof-catalog entry**, and (when it uses one) a
**system-design pattern entry**. It is the output side of `ai-native-engineering.md` (the No-Black-Box
debrief) and `documentation.md` (the as-built map).

## Pillar 1 — the 9-step case study (the architect's dossier)

Every Path-B/C workstream (and any instructive Path-A fix) gets a case study. The two steps that separate
*a technician who knows tools* from *an engineer who makes decisions* are **#3 Options** and **#4
Trade-offs** — never skip them. Template → `docs/evidence/case-study-template.md`; case studies live at
`docs/evidence/case-studies/<slug>.md` (+ an org-site pointer):
```
1. BUSINESS PROBLEM     the real driver (not "I wanted to learn X")
2. CONSTRAINTS          scale, consistency, auditability, downtime, cost, regulation
3. OPTIONS              2–3 real alternatives considered
4. TRADE-OFFS           why each wins/loses against the constraints
5. DECISION             what we chose + why (links the ADR)
6. IMPLEMENTATION       the shape (resources, data, flow); where state/secrets live
7. FAILURE              what happens when a dep dies; how it rolls back (link the Game Day/postmortem)
8. MEASUREMENT          the numbers (latency, throughput, MTTR, RPO/RTO, coverage, €/req)
9. LESSON LEARNED       what you'd do differently; what transferred
```
Problem-first, always: a feature starts from *"Claims must process many events asynchronously — what
architecture fits?"* → then NATS/Kafka — never *"I want to learn Kafka."*

## Pillar 2 — the proof catalog (the competency → proof matrix)

A single running register `docs/evidence/proof-catalog.md` (seeded) mapping each competency to its
**concrete proof** (a case study, a postmortem, a PR, a live demo, an eval run). The target is **30–50
proofs by end of year.** Columns: `Competency · Proof (what + link) · Evidence (metric/artifact) · Status`.
Covers: Backend · Distributed systems · Kubernetes · GitOps · Cloud · Security · SRE · Data · AI ·
Architecture · Problem-solving · Communication · Business/ROI. Grooming it is a quarterly ritual
(`productization.md` cadence) — it IS the portfolio index.

## Pillar 3 — the system-design pattern catalog (interview prep)

Classic system-design interviews ask you to *design X* and *explain pattern Y + its trade-offs*. This
platform already **implements** most of them for real — so each pattern has a **proof you built**, not
theory. Register → `docs/evidence/system-design-patterns.md` (seeded, rich). Per pattern:
`Pattern · Problem it solves · Trade-offs · Where in ktayl (the proof) · 30-second interview framing`.
It also carries **design drills** — the "design a claims system / an event consumer that survives a 10k
backlog / enterprise DR / an enterprise LLM gateway / multi-team deploy with guardrails" questions,
answerable from *what you actually built*. **Discipline: when you build with a pattern, add/append its
catalog row with the proof + the framing** — in the same effort (a DoD item, like the as-built doc).
Kept as a **consulted doc** (not auto-loaded) so it can grow rich without bloating session context; study
it before interviews.

## The claim this licenses
> *"Over a year I designed and operated a fictional insurer as if it had to really run — business apps,
> cloud platform, security, IAM, data, AI, legacy integration, observability, incidents and DR — and I
> can show the architecture, the trade-offs, the postmortems and the numbers for each."*

That is a far stronger story than a project size or a tool count, and it maps directly to the target
profile (Software + AI + Platform + Enterprise problem-solver).

## Publish pipeline (reputation compounding)
Each strong case study → a **LinkedIn / portfolio** post framed as a problem, not an install log
(*"How I designed DR for a self-hosted insurance platform"* / *"Integrating a legacy SOAP core with an
event-driven architecture"* / *"What happens when you intentionally kill a workload in an insurance
platform?"*). Builds a reputation around **AI × Platform Engineering × Enterprise Architecture × Insurance**.
Portfolio structure + positioning: `[[feedback_portfolio_positioning]]`.

## Discipline
- **No proof without a number or an artifact** — "it works" is not evidence; a graph/log/metric/PR is.
- **Options + Trade-offs are mandatory** — that's the problem-solver signal.
- **One source of truth** — the ADR holds the decision; the case study holds the story; the proof-catalog
  indexes it; don't duplicate the body, link it.
Related: `documentation.md`, `ai-native-engineering.md`, `reliability-and-gamedays.md`, `synthetic-enterprise.md`.
