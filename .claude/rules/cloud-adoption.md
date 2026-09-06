# Cloud Adoption — need-first, free-tier, justified (decision rule)

**We do not adopt cloud to "learn cloud."** Every cloud capability must solve a **real,
current need** of one of the two layers, with a **business + compliance justification**.
The skill gained is a *byproduct* of doing real work — the same way k8s was learned. This
rule is the gate; specific use cases are picked **when they become real**, not up front.

## The two layers (never conflate — see `github-projects.md`)
- **ktayl-solution IS** = the insurance organisation's IS (business context) → Portfolio #1,
  documented in ktayl / `minicloud-platform-docs`.
- **Retrieva** = the RNCP39583 certification project (DORA product) that runs on the IS →
  Certification #2, documented in Retrieva's own docs (`retrieva/docs/docs/certification/`).

## The decision gate — before adopting ANY cloud resource, all must hold
1. **Real need.** It closes a genuine gap that exists *today* in ktayl-IS or Retrieva — not a
   hypothetical or a tutorial. If you can't name the gap, don't build it.
2. **Justification.** There is a one-line "because…" a reviewer/interviewer would accept —
   ideally **regulatory** (DORA, EU AI Act, GDPR, Solvency II, BaFin VAIT) or a concrete
   architecture/business driver. "I put X on AWS **because** DORA Art. 11 mandates off-site DR."
3. **Free / in-cap.** Uses an **always-free tier** (preferred) or stays within the €10/mo/provider
   hard cap ([[project_aws_budget_principle]]). Prefer always-free over 12-month-trial; never let
   a trial resource run past month 12.
4. **Layer-routed.** It clearly belongs to ktayl-IS **or** Retrieva, and is documented in that
   layer's docs (ADR / runbook), not the other's.
5. **Terraform + destroyable.** Defined as IaC in `minicloud-cloud`; teardown is one command.
   Managed-k8s (EKS/AKS/GKE) and other paid-node/paid-hour services are **ephemeral only**
   (`apply → capture evidence → destroy`), never left standing.

If a candidate fails any gate → **park it** (note it below), don't build it.

## Guardrails (hard, always)
- **€1 budget alert** on every cloud account (AWS/Azure/OCI/GCP) — set *before* the first resource.
- **No money-pits standing:** NAT gateways, standing managed-k8s nodes, load balancers you don't
  need, egress over free limits, standing managed DB.
- **OCI caveat:** idle instances get reclaimed (keep the free ARM VM lightly active); ARM capacity
  can be scarce (retry / quieter region).
- Every adoption ends in an **ADR or runbook** (evidence > tools) — the "because…" written down.

## Why multi-cloud here is a *feature*, not a spread
An insurer is **legally required** to have off-site DR (DORA Art. 11–12) and to manage
**cloud-concentration risk** (DORA Art. 28–29). So ktayl-IS spanning bare-metal + real cloud
providers is **meeting a regulatory requirement**, and **Retrieva is the tool that proves it's
met** — a closed loop. Deliberate, justified multi-cloud = senior competency; the same shallow
thing on two clouds = a spread. Keep each provider in a **distinct lane** (see the career strategy
in [[user_career_goals]]): AWS (serverless/IAM), Azure (enterprise identity/managed-k8s/CI),
OCI (always-on free compute node), GCP (free GPU for ML + free Gemini/Gemma via LiteLLM).

## Candidate needs backlog (spotted, NOT yet triggered — apply the gate when one becomes real)
| Real need (gap today) | Layer | Likely cloud piece | Justification |
|---|---|---|---|
| Off-site DR backup (all backups are single-site on controller MinIO) | ktayl IS | AWS S3/Glacier target | DORA Art. 11–12 business continuity |
| Second-provider DR/failover (no cloud concentration) | ktayl IS + Retrieva | OCI free ARM node | DORA Art. 28–29 (Retrieva's own thesis, lived) |
| External customer identity (Authentik is staff-only) | ktayl IS | Azure Entra B2C (free 50k) | workforce vs customer identity separation |
| Credible SaaS hosting/residency story for EU customers | Retrieva | Azure/AWS managed front | a DORA-compliance SaaS needs a real residency story |
| GPU for embeddings/eval/fine-tuning (vLLM is CPU-only, slow) | Retrieva | GCP Kaggle free GPU | RAG quality + ML-fundamentals (career gap 6) |

These are **not commitments** — they're pre-vetted candidates. Pick one only when its need is
genuinely pressing, then run the decision gate, build it in `minicloud-cloud`, and write the ADR.
