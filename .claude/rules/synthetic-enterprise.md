# Synthetic Enterprise — ktayl is a simulation, proven by operation (not by real users)

ktayl-solution is a **fictional insurer used as an enterprise-architecture + engineering laboratory**.
There are **no real customers and no production insurance operations**. That is a *strength, not a
weakness* — provided we replace "real users" with **realistic proof of operation**. This rule defines how.

> **The honest framing (publish it, don't hide it).** Every public surface (portfolio, org-site, a demo)
> carries the disclaimer verbatim:
> *"ktayl is a fictional insurance company used as an enterprise-architecture and engineering laboratory.
> No real customer data or production insurance operations are involved. The platform uses synthetic
> data, automated business workflows, simulated users, load testing and controlled failure scenarios to
> reproduce realistic enterprise operating conditions."*
> Claiming real traction we don't have is the one thing that destroys credibility. We claim **engineering
> proof**, not commercial traction.

## The four levels of realism (what replaces "real users")

```
                 KTAYL (synthetic enterprise)
      ┌──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
 synthetic data  behavioral load  simulated ops  external validation
 (seed volumes)  (traffic w/ a    (role workflows (5–20 domain experts
                  daily shape)     via API/Playwright) test ONE brick)
```

1. **Synthetic data with volume** — thousands of policyholders, policies, claims, payments, brokers,
   suppliers, documents, events. Deterministic + reproducible (seed-based); PII is **synthetic by
   construction** (never real).
2. **Behavioral load, not static data** — the generator reproduces a *business day shape*
   (`09:00 policy lookups ↑ · 09:17 payment batch · 10:00 a suspicious claim · 11:00 doc ingestion …`),
   so the platform is **continuously exercised as if used**.
3. **Simulated operators** — role personas (Claims Agent · Underwriter · Broker · Finance · IT-Operator ·
   Security-Analyst · Compliance-Officer) each running their real workflow
   (`broker → quote → underwriting → bind → payment → claim → investigation → settlement`) via **API
   clients / Playwright**, on a schedule.
4. **External validation (the one real-user layer)** — get **5–20 real insurance professionals** to test
   a *single brick* (e.g. the Claims Workbench) for 30 min. Yields **expert validation** (workflow / UX /
   vocabulary / completeness), logged in the validation log (`productization.md`) — a different, honest
   proof than "production usage".

## The component — `ktayl-simulator` (need-first; the standard, not yet built)

A dedicated workload that **drives** the synthetic enterprise. **Build it when the spine has ≥2 live
domains to exercise end-to-end** (Policy + Claims already qualify; Billing makes it compelling). Until
then this rule is the contract; don't scaffold it empty (the need-first gate, like `ktayl-core`).

Shape: a scheduler + per-domain **workload scripts** (seed → behavioral traffic) + per-role **operator
scripts** (API/Playwright journeys) → drives the real dev/prod APIs → emits/consumes the real domain
events. It is **synthetic input**, never a mock of the system under test. Home: its own repo
`ktayl-simulator` (it runs in a container + is unit-tested → code repo, per `conventions.md`), deployed
as CronJobs/Deployments via gitops. It MUST hit the **dev** environment by default (never fabricate load
against prod without intent), and tag its traffic (`x-synthetic: true` header / a `simulator` user-agent)
so it's filterable in observability.

## The KPI scorecard it feeds (measure, don't assert)

The simulator exists to make these **measurable and live** — the register is `docs/evidence/kpi-scorecard.md`
(seeded, updated as domains go live). Three families:

| Family | Example KPIs | Source |
|---|---|---|
| **Business** | policies/day · claims/day · avg claim-processing time · payment-processing time · premium-to-cash lead time · (later) fraud-detection rate | domain DBs + events |
| **Technical** | p95 latency · throughput · error rate · availability · deployment frequency · **MTTR · RPO/RTO** · event-processing lag | Prometheus/Grafana/Loki + the `sdlc_loop` bands |
| **AI** | retrieval accuracy · hallucination rate · agent success rate · **cost/request** · latency · human-escalation rate | Langfuse / LiteLLM (see `llmops.md`) |

**The claim this licenses (interview-ready):** *"I built a synthetic enterprise that generates realistic
insurance workloads and continuously exercises the platform; I measure its reliability, security,
performance and business workflows under normal AND failure conditions."* — engineering proof, honestly scoped.

## How it ties into the rest
- The **failure conditions** half of that claim is `reliability-and-gamedays.md` (Game Days drive the
  simulator *during* an induced incident → MTTR/RPO/RTO become real numbers).
- Each simulator-proven capability becomes a **case study + a proof-catalog entry** (`evidence-and-proof.md`).
- A brick that experts validate (level 4) is the on-ramp to `productization.md`.
- Keep it **synthetic + disclaimed + dev-first + tagged**; never blur synthetic load with a real-traction claim.
