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

## The 3-tier free model — build *permanent* only on always-free

"Free" is three different things with three different lifespans. Conflating them is how a homelab
ends up with a surprise bill or an outage in month 13. **Anything permanent, stateful, or always-on
MUST sit on the always-free tier; the other two tiers are for second copies and bursts only.**

| Tier | Lifespan | Primitive examples | Use it for |
|---|---|---|---|
| **Always-free (perpetual)** | forever, within limits | OCI A1.Flex VM · Lambda/Functions · DynamoDB/Cosmos 25 GB · Cloudflare R2 10 GB · CloudFront/Static Web Apps · Workers/Cloud Run | **the permanent hybrid architecture** (DR anchor, external monitor, status page, offsite backup target) |
| **12-month free** | **expires month 13** | Azure VM 750 h · Blob 5 GB · Postgres B1MS · ACR · AWS EC2 t2.micro 750 h | **second copies / bonus** — disposable, never load-bearing |
| **Credits** | until spent / dated | **$100 Azure Education** (exp 2027-09-23) · AWS credits | **bursts** — DR game-days, ephemeral bigger VMs, AI-service experiments (`apply → evidence → destroy`) |

**Rule:** if losing the resource at the tier's cliff would degrade the platform, it's on the wrong
tier — move it to always-free or don't depend on it. Managed-k8s / paid-node / paid-hour services stay
**ephemeral only** (gate #5). The `$100` Education credit is ~$8/mo — treat it as burst fuel, not a budget.

## Our accounts — which one plays which tier (they are NOT interchangeable)

We hold four provider accounts. **One has no credit shield** — mixing them up is how a mistake bills.

| Account | Shield | Tier role | Runs | Guardrail |
|---|---|---|---|---|
| **Azure PAYG** (acct 1, sub `<payg>`) | **none — bills day 1** | **always-free services ONLY** | permanent Azure always-free (Functions/Cosmos/Static Web Apps/Container Apps/Arc) | €15 sub budget (`budgets.tf`); never a standing paid resource; **verify its 12-month-free window isn't already spent** (it runs Azure OpenAI since 2026-08, so likely gone → treat 12-month tiers on it as **paid**) |
| **AWS** (acct 2) | credit → then always-free | permanent serverless anchor | Anchor 1 heartbeat (Lambda + DynamoDB + CloudFront) — all always-free | €15 budget (`budgets.tf`) |
| **Azure Education** (acct 3, sub `<edu>`, exp **2027-09-23**) | $100 (~$8/mo) | **burst fuel only** | ephemeral DR game-days, AI experiments (Document Intelligence / Vision) — `apply → evidence → destroy` | its **own** budget on its subscription (`azure-education-budget.tf`); pin bursts to `TF_VAR_azure_education_subscription_id` |
| **OCI** (acct 4, ADR-0001) | always-free | always-on free compute | DR node / restore target | €1 tripwire (`oci-budget.tf`) |

**Two hard rules from this map:**
1. **PAYG = always-free only.** The no-credit account is the one where a mistake costs euros immediately.
2. **Education is a *separate subscription*** — every burst resource pins `TF_VAR_azure_education_subscription_id`, **never** `azurerm_subscription.current` (that is PAYG). It carries its own budget alert; `budgets.tf` does **not** cover it.

## Always-free service map (the durable primitives — check candidates against this)

The permanent layer is **serverless + a tiny managed store + free CDN/egress + an always-free VM**, not
always-on paid VMs. What is genuinely always-free per lane (verify current terms before depending):

- **OCI** *(always-on compute lane)* — **A1.Flex 4 OCPU / 24 GB Arm** + 200 GB block (our DR node,
  ADR-0001) · 2× AMD micro VMs · 10 GB object · 10 TB/mo egress.
- **AWS** *(serverless/IAM lane)* — **Lambda 1M req + 400k GB-s** · **DynamoDB 25 GB** · SNS/SQS 1M ·
  **CloudWatch 5 GB logs/10 metrics** · **CloudFront 1 TB egress + 10M req** · EventBridge · Cognito 10k MAU.
  *(S3 5 GB is 12-month, NOT always-free — use R2 for permanent object storage.)*
- **Azure** *(enterprise identity / CI lane)* — **Functions 1M req** · **Container Apps 180k vCPU-s / 2M req** ·
  **Cosmos 25 GB + 1000 RU/s** · **Static Web Apps 100 GB** · Monitor 5 GB logs · Event Grid 100k · API Mgmt 1M ·
  Entra ID 50k objects · Azure Arc · Cost Mgmt/Policy/Advisor. *(VM 750 h, Blob 5 GB, Postgres 750 h = 12-month.)*
- **Cloudflare** — **R2 10 GB + ZERO egress** (best permanent object store of all lanes; already core) ·
  Workers 100k req/day · Pages (static) · Tunnel.
- **GCP** *(free GPU/ML lane)* — e2-micro always-free VM (1 region) · Cloud Run 2M req · Kaggle/Colab free GPU.

## The exit test (per resource, written down — sharpens gate #5)

For **every** cloud resource, write the one command that **turns it off** and the check that **the laptop
cluster is unaffected**. If you can't write both, you've created a hidden dependency — **don't ship it.**
This is what keeps "teardown is one command" honest and what makes a 12-month/credit resource safe to use:
it's only a *bonus* if its removal is a no-op to the primary platform. Record the exit test in the resource's
ADR/runbook next to the "because…". (Reference: ADR-0001's `enable_oci_dr_node=false` one-flag teardown.)

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
