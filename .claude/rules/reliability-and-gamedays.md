# Reliability as Evidence — SLOs, Game Days, incidents, postmortems

**The constraint (always-on):** "how do you *know* it's reliable?" is answered with **SLO → SLIs → error
budget → alerts → incident response → postmortem → chaos testing**, not *"I run Kubernetes."* In a
synthetic enterprise (`synthetic-enterprise.md`) we **induce** failures, measure recovery, and write it
up — that operational trace is our strongest problem-solver evidence.

## SLO register — mandatory per prod-grade service
A service is not "done" without an **SLO contract** (not just dashboards) in `docs/reliability/slo-register.md`:
**SLIs** (availability/p95-latency/event-lag) · **SLOs** (*modest + honest*, lab-sized) · **error budget**
(`1 − SLO`; burn → freeze risky changes) · **RTO/RPO** for stateful (proven by a DR drill). Checked at the
**QA gate** + the Definition of Done; `sdlc_loop` bands are the always-on SLI watcher.

## Failure-scenario catalog (reference — the standing Game Day set)
Scenarios 01 baseline · 02 traffic ×10 · 03 DB down · 04 NATS down · 05 bad deploy · 06 security · 07 AI
failure · 08 DR (full table + hypotheses in `docs/reliability/slo-register.md` §Scenarios).

## Discipline
- **Modest, honest SLOs** (a met lab target beats a faked 99.99%).
- **Induce on dev first**; a prod Game Day is deliberate + announced.
- **Every Game Day ends in a postmortem + a KPI-scorecard update** — an induced failure with no write-up is wasted evidence.
- **Don't double-count** the gates: CI proves code, the QA gate proves the live dev service, this proves it **under failure** — distinct evidence.

> **HOW to run one → the `run-game-day` skill** (the Detect→…→Postmortem loop, the scenario induce-steps,
> the blameless postmortem template, run-simulator-during-the-incident for real MTTR/RPO/RTO). Pulled on
> demand when exercising a scenario or writing a postmortem.

Related: `synthetic-enterprise.md`, `evidence-and-proof.md` (postmortem = a proof), `offsite-dr-backup`
skill (DR restore path), `scheduling.md`, `gitops.md` (the canary brake).
