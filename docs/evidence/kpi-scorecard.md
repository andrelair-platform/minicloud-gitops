# KPI Scorecard — the synthetic enterprise, measured

Made live + measurable by the `ktayl-simulator` (`.claude/rules/synthetic-enterprise.md`). Until the
simulator runs, these are the **targets to instrument**; fill the "Current" column as each domain goes
live. Sources: domain DBs/events · Prometheus/Grafana/Loki + `sdlc_loop` bands · Langfuse/LiteLLM.

## Business KPIs
| KPI | Target (lab) | Current | Source |
|---|---|---|---|
| Policies bound / day | simulated shape | — | PAS + UW events |
| Claims / day | simulated shape | — | claims DB |
| Avg claim-processing time | baseline then ↓ | — | claims events |
| Premium → cash lead time | measured | — | ktayl-core Billing |
| Payment-processing time | measured | — | Billing + Stripe(test) |

## Technical KPIs
| KPI | Target (lab) | Current | Source |
|---|---|---|---|
| Availability (per SLO service) | per `slo-register.md` | — | Prometheus |
| p95 latency | < 300 ms (API) | — | Prometheus |
| Error rate | < 1% | — | Prometheus |
| Deployment frequency | track | — | ArgoCD/Kargo |
| MTTR | measured in Game Days | — | postmortems |
| RPO / RTO | per service | authentik RTO ~9 min | DR drills |
| Event-processing lag | < 60 s | — | NATS/JetStream |

## AI KPIs
| KPI | Target | Current | Source |
|---|---|---|---|
| Retrieval accuracy | track | — | Langfuse eval |
| Hallucination rate | ↓ | — | Langfuse eval |
| Agent success rate | track | — | Langfuse |
| Cost / request | bounded | metered | LiteLLM |
| Human-escalation rate | track | — | app |

**Discipline:** a KPI without a source + a number is a wish. Each Game Day (`reliability-and-gamedays.md`)
updates the technical rows with *measured* values.
