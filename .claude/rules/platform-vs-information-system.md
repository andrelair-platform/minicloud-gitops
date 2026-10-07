# Platform vs Information System — the two operating layers (STRICT distinction)

The stack has **two distinct layers — never conflate them.** This is the single most important
architectural boundary; every artifact (a service, a doc page, a repo, a namespace, a board item) belongs
to **exactly one** of them.

| Layer | What it is | Owns it (real-enterprise) | Domain-specific? |
|---|---|---|---|
| **PLATFORM (minicloud)** | the technical **capabilities** — compute, networking, storage, registry, delivery (GitOps/CI/Kargo), secrets, **identity-as-a-service**, observability, **AI platform**, **data platform**, cluster security | Platform Engineering / Cloud & Infra / SRE (the internal "cloud provider") | **No** — agnostic (sell insurance or shoes, it's the same platform) |
| **INFORMATION SYSTEM (ktayl-solution)** | the **applications + data + processes** that run the insurer — policy, claims, underwriting, billing, the **digital workplace** (mail/files/chat), ERP, ITSM, IAM **governance**, the **regulatory** obligations, business data products | DSI + business domains + Enterprise Architecture + Compliance | **Yes** — it *is* the insurance business |

> **Orthogonal to the OTHER two-layer.** `github-projects.md` defines a *different* axis: the **IS (org
> context) vs Retrieva (the RNCP39583 cert deliverable)**. That is org-vs-cert; **this** rule is
> infra-vs-business. A thing is therefore one of: **Platform** (infra) · **IS** (business app) ·
> **Retrieva** (cert product that *runs on* both). Don't mix the two axes.

## The distinction in one line
> **Platform = PROVIDES capabilities. IS = CONSUMES them to deliver insurance business value.** Provider ↔ consumer.

## Litmus tests — apply to ANY artifact before filing it
1. **The gold test:** *"If ktayl stopped selling insurance tomorrow, would this survive unchanged?"*
   **Yes → Platform** (it's infrastructure). **No → IS** (it's the business/employees/regulator).
2. **Provider vs consumer:** does it *provide* a capability (Platform) or *use* one to make business value (IS)?
3. **Who owns/pages it:** Platform-Eng/SRE → Platform; a business domain / Corporate-IT / Compliance → IS.

## Capability vs Use — the #1 source of confusion (the straddle rule)
**Separate the CAPABILITY (a shared service = Platform) from its BUSINESS USE / GOVERNANCE (= IS).** A tool
appears **once** as a Platform capability; its business application/governance lives in IS and **cross-links** to it.

| Brick | Platform (the capability) | IS (the business use / governance) |
|---|---|---|
| **Authentik** | SSO-as-a-service every app trusts | identity **governance** (joiner/mover/leaver, access requests, IGA — ktayl-iam) |
| **Mail / Nextcloud / Matrix / Jitsi** | running the services on k8s | the **Digital Workplace** (employee collaboration) |
| **Postgres / CNPG** | Postgres-as-a-service, backup, the standard | the business **schema** + data |
| **AI (LiteLLM / Qdrant / Langfuse)** | the gateway + RAG + LLMOps infra | **AI products** (e.g. Retrieva, an assistant) |
| **Data Platform (Kafka/ClickHouse/dbt/OpenMetadata)** | shared data-infra (ingest/OLAP/transform/catalog) | **data products** (`policy_portfolio`, insurance BI) |
| **Security** | cluster hardening, Gatekeeper, supply-chain, SSO-infra, secrets-infra | **regulatory compliance** (GDPR/DORA/ACPR), data classification, employee credential mgr |

## Where the distinction is ENFORCED (filing consequences)
- **Docs (org site `minicloud-platform-docs`) = two pillars:** `platformSidebar` (Platform) + `isSidebar`
  (IS). **File by pillar, and the file namespace MUST match the pillar:** IS pages → **`is/`** or
  `insurance-platform/`; Platform pages → `developer-platform/`, `security-enterprise/`, `observability/`,
  `ai-ml/`, `data-layer/`, etc. **Never file an IS page under a Platform namespace** (the mistake fixed in
  the 2026-10-07 reclassification: 20 IS pages were under `developer-platform/` → moved to `is/`). A
  capability-vs-use straddler: put the **capability page in Platform**, **cross-link** the business use from IS.
- **Repos / boards** (`github-projects.md`): Platform repos (`-gitops/-ansible/-opentofu/-backstage/-ops`)
  → *GitOps — Platform Engineering* (#3); IS business domains → their product boards.
- **Namespaces / deploy:** shared infra in platform namespaces; business apps in their domain namespaces.

## Reference application (canonical)
The **2026-10-07 Platform/IS reclassification** (minicloud-platform-docs): Retrieva removed from org docs
(it has its own docs) · **Data Platform → Platform pillar** (shared data-infra, twin of the AI platform) ·
**20 IS pages `developer-platform/` → `is/`** · AI-governance regrouped · cluster-security = Platform while
regulatory-compliance = IS. That is the worked example of this rule.

## Don't
- Don't file business apps / data products / AI products under a **Platform** namespace, or cluster/infra
  security under **IS**, or regulatory compliance under **Platform**.
- Don't duplicate a straddling tool into both pillars — **capability in Platform, cross-link the use from IS**.
- Don't conflate this axis (Platform ↔ IS) with the cert axis (IS ↔ Retrieva, `github-projects.md`).

Related: `github-projects.md` (the cert axis + boards), `project-governance.md` (SA artefacts), `architecture-strategy.md` (modular monolith = an IS-build rule), `workplace-architecture.md` (the Digital Workplace = IS), `documentation.md` (docs-as-map).
