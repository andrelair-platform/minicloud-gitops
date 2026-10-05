# SLO Register + Game Day Catalog

Per `.claude/rules/reliability-and-gamedays.md`. Modest, honest targets sized to a 5-node lab. Seeded
with the live services; add a row when a service reaches production-grade. The always-on SLI watcher is
the controller `sdlc_loop` control-band detector.

## SLOs (per service)
| Service | SLI(s) | SLO target | Error budget (window) | RTO / RPO |
|---|---|---|---|---|
| ktayl-policy-service (PAS) | availability; p95 | 99.0% ; p95 < 300 ms | 1% / 30d | RTO 30m / RPO 24h (CNPG) |
| ktayl-claims | availability; event lag | 99.0% ; lag < 60 s | 1% / 30d | RTO 30m / RPO 24h |
| ktayl-underwriting | availability; p95 | 99.0% ; p95 < 400 ms (rating) | 1% / 30d | RTO 30m / RPO 24h |
| ktayl-iam | availability (auth path) | 99.5% | 0.5% / 30d | RTO 15m / RPO 24h |
| ktayl-core (Billing) | ingest lag; GL-post success | lag < 60 s ; 100% balanced JE | — | RTO 30m / RPO 24h |
| authentik (SSO) | availability | 99.5% | 0.5% / 30d | **RTO ~9 min (drill-proven)** / RPO 24h |

> Targets are **starting hypotheses** — tighten once the simulator produces a real baseline. A met modest
> SLO beats a faked aggressive one.

## Game Day scenario catalog
Run each as `Detect → Diagnose → Mitigate → Recover → Measure → Postmortem`, with the simulator driving
load *during* the incident so MTTR/RPO/RTO are measured, not estimated. Write-ups →
`docs/reliability/postmortems/`.

| # | Scenario | Induce with | Hypothesis | Last run |
|---|---|---|---|---|
| 01 | Normal ops baseline | simulator | SLOs green; capture baseline | — |
| 02 | Traffic spike ×10 | simulator burst | autoscale/degrade, no 5xx storm | — |
| 03 | DB unavailable 15 min | Chaos Mesh / scale CNPG→0 | clean degrade, alert, recover, no data loss | — |
| 04 | NATS down | Chaos Mesh | JetStream persists → lag → KEDA → drain | — |
| 05 | Bad deployment | broken image | canary analysis auto-aborts | — |
| 06 | Security incident | leaked secret / rogue workload | Gatekeeper deny / Vault rotate; audited | — |
| 07 | AI failure | LLM down / bad output | gateway fallback; eval catches it | — |
| 08 | Disaster recovery | destroy node/cluster | restore within RTO; verify RPO | — (authentik restore drill ✅) |

**Priority first runs:** 03 (DB), 04 (NATS backlog → KEDA), 08 (full DR) — the three highest-signal
proofs for the proof-catalog.
