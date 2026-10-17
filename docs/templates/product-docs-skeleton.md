# Canonical per-product `docs/` skeleton

> **Template.** The ONE reconciled layout for every product's `docs/` — so products stop varying
> (`documentation-standard.md` G3). It reconciles the **SA artefact set** (`project-governance.md` #1–8)
> with the **documentation taxonomy checklist**. Scale by delivery path: a Path-A change adds nothing; a
> Path-C product grows the whole tree. **Platform concerns are referenced, never restated.**

## The tree (create a folder the day its category applies — not before)

```
<repo>/docs/
├── prd.md                           # (1) Product contract — problem, users, scope, NFR, security, compliance, cost   [B/C]
├── architecture/
│   ├── solution-architecture.md     # (2) the SDD — assembles #1–#8 into one blueprint                                [C]
│   ├── c4-container.md              # (2) C4 context+container (diagrams-as-code / Structurizr)                       [C; B: context]
│   ├── adr/                         # (2) Architecture Decision Records → auto-indexed on the central site
│   │   ├── 000-index.md
│   │   └── ADR-00x-<decision>.md
│   └── img/                         #     generated diagram SVG/PNG (committed; diagrams-as-code.md)
├── data-model/                      # (2/7) tbls ERD baseline + .tbls.yml → auto-generated + drift-gated              [if it has a DB]
│   ├── README.md
│   └── <schema>.<table>.md
├── api/
│   └── openapi.yaml                 # (4) the API contract (+ L3 contract tests validate it)                          [if it exposes an API]
├── specs/
│   └── spec-<epic>/SPEC.md          #     per-epic implementation contract (+ stories.yaml)                           [B/C]
├── traceability-matrix.md           # (5) requirement ID → component → test → pipeline → evidence                    [C]
├── runbooks/                        # (6) operational procedures (incidents + recurring tasks)                        [prod-grade]
│   └── <task>.md
├── slo.md                           # (6) this product's SLIs/SLOs/error-budget/RTO-RPO (the per-product SLO entry)   [prod-grade]
├── security/
│   └── threat-model.md              # (7) STRIDE-lite + mitigations + data classification                            [C / boundary change]
├── ai/                              # (9) ONLY if the product calls an LLM
│   ├── evaluation.md                #     eval strategy + golden-set + results (hallucination/grounding/robustness)
│   ├── model-card.md                #     model(s) used, capabilities, limits, disallowed uses
│   └── prompts.md                   #     prompt versions/labels + change log (Langfuse-managed; Git = seed/fallback)
└── AGENTS.md  (repo root, not docs/)#     tiny agent-context block — policy/command-catches/pitfalls (NOT an overview)
```

## What is DELIBERATELY not here (it's Platform-level → reference it, don't copy it)
CI/CD + GitOps + Kargo promotion (`gitops.md` / the zero→prod runbook) · secrets ESO→Vault · SSO/Authentik
(`security-enterprise/sso-authentik`) · observability stack · backup/DR mechanics · supply-chain
(cosign/SBOM/Trivy). The product's docs **link** these standards; restating them is the anti-pattern
(`platform-vs-information-system.md` + `documentation.md` "link, don't duplicate").

## Reconciliation note (why not the generic `docs/01-07/` tree)
The generic numbered tree (01-product … 07-security) duplicates the SA artefact set and the central
docs-as-map, and has no place for platform-level cross-cutting docs. This skeleton keeps the SA set as the
spine, folds the taxonomy categories in as **optional, need-gated folders**, and leaves platform concerns
where they belong — one standard, linked. Reference products: **ktayl-core** (plain `docs/`) and
**retrieva** (Docusaurus `docs/docs/`).

## Mandatory pairing (don't forget)
Every doc here gets a **map entry on the central site** (`minicloud-platform-docs`) that summarises + links
it (`documentation.md`). ADRs and the ERD are auto-indexed (no manual pointer); everything else needs the
one-line pointer page.
