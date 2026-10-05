# Reliability as Evidence — SLOs, Game Days, incidents, postmortems

"How do you *know* the system is reliable?" is never answered with *"I run Kubernetes."* It's answered
with **SLO → SLIs → error budget → alerts → incident response → postmortem → chaos testing**. In a
synthetic enterprise (`synthetic-enterprise.md`) we don't wait for a real user to find a failure — we
**induce** it, measure the recovery, and write it up. That operational trace is the strongest
problem-solver evidence we produce. Built on what's already live: **Chaos Mesh** (fault injection),
**Velero + CNPG + raft snapshots** (backup/restore), **Prometheus/Grafana/Loki/Alertmanager**, and the
controller **`sdlc_loop`** control-band detector.

## 1. SLO register — every production-grade service declares its targets

A service is not "done" without an **SLO contract** (not just dashboards). Register:
`docs/reliability/slo-register.md` (seeded with the live services). Per service record:
- **SLIs** — the measured signals (availability = success/total; latency = p95; freshness = event lag).
- **SLOs** — the target (e.g. `99.0% availability`, `p95 < 300ms`, `event lag < 60s`) — *modest + honest*,
  sized to a 5-node lab, not copied from a hyperscaler.
- **Error budget** — `1 − SLO` over the window; what happens when it's burned (freeze risky changes).
- **RTO / RPO** — for stateful services (how fast we recover, how much data we can lose) — proven by a DR drill.

The SLO is checked at the **QA gate** (`qa-gate.md`) + is part of the Definition of Done
(`agile-execution.md`). `sdlc_loop` bands are the always-on SLI watcher.

## 2. The failure-scenario catalog (Game Days)

A standing set of **induced failures**, each run as a Game Day and written up. Seeded catalog
(`docs/reliability/slo-register.md` §Scenarios):

| # | Scenario | Induce with | Expected behaviour (the hypothesis) |
|---|---|---|---|
| 01 | Normal operations (baseline) | the simulator | SLOs green; baseline KPIs captured |
| 02 | Traffic spike ×10 | simulator burst | autoscale (KEDA) / graceful degradation, no 5xx storm |
| 03 | Database unavailable (15 min) | Chaos Mesh / scale CNPG to 0 | app degrades cleanly, alerts fire, recovers, **no data loss** |
| 04 | Event broker (NATS) down | Chaos Mesh | events accumulate (JetStream persists), consumer lag → KEDA scales, backlog drains on recovery |
| 05 | Bad deployment | push a broken image | canary/BlueGreen Rollout + analysis **auto-aborts**; no bad version serves |
| 06 | Security incident | leaked secret / unauthorized workload | Gatekeeper denies / rotate via Vault+ESO; audit shows it |
| 07 | AI failure | LLM down / bad answers | AI gateway fallback; eval catches regression; human-escalation path |
| 08 | Disaster recovery | destroy a node / cluster | restore from Velero/CNPG/raft within **RTO**; verify **RPO** |

**Each Game Day follows the loop:** `Detect → Diagnose → Mitigate → Recover → Measure → Postmortem`.
Run the **simulator during** the incident so MTTR / RPO / RTO / error-rate are **real measured numbers**,
not estimates.

## 3. Postmortem template (blameless — copy per incident/Game Day)

Lives at `docs/reliability/postmortems/<date>-<slug>.md`:
```
# Postmortem — <title>  (<date>, induced | real)
Summary        one paragraph: what happened, impact, duration.
SLO impact     which SLI breached, error-budget burned, MTTR.
Timeline       detect → diagnose → mitigate → recover (timestamps).
Root cause     the actual layer + why (not the symptom).
What worked    the controls/automation that helped.
What didn't    gaps (missing alert, slow runbook, wrong assumption).
Action items   concrete fixes, each an owner + issue link.
Evidence       graphs, logs, kubectl output, the restore proof.
```
A postmortem is a **proof-catalog entry** (`evidence-and-proof.md`) — the clearest signal of the
"operate under failure" competency.

## 4. Discipline
- **Modest, honest SLOs** — a lab target met is worth more than a 99.99% target faked.
- **Induce on dev first**; a prod Game Day is deliberate + announced.
- **Every Game Day ends in a postmortem + an updated KPI scorecard** — an induced failure with no write-up
  is wasted evidence.
- **Don't double-count** the existing gates: CI (`testing.md`) proves code; the QA gate (`qa-gate.md`)
  proves the live dev service; this proves it **under failure**. All three are distinct evidence.

Related: `synthetic-enterprise.md` (drives load during incidents), `evidence-and-proof.md` (write-ups →
proofs), `ops-runbooks` + `scheduling.md` (the existing operational runbooks), `gitops.md` (the canary brake).
