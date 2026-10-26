# Software Evaluation Scorecard — `<tool / capability being chosen>`

> Fillable template for the weighted-scoring step of `.claude/rules/software-evaluation.md`. Copy it,
> fill it per evaluation, commit the filled copy to the owning repo's `docs/` (or the IS docs for an
> org-wide tool), and record the live evaluation in **Retrieva** (the tool of record). Scale to the
> delivery path: a Path-A utility doesn't need this sheet; a Path-C / boundary / P0–P3 tool does.

## 0. Header

| Field | Value |
|---|---|
| Capability / gap being filled | `<the named current gap — step 1>` |
| Delivery path | `A / B / C` |
| Evaluator(s) + date | `<who, YYYY-MM-DD>` |
| Layer | Platform capability / IS business app |
| DORA third-party-ICT class | `<supporting / important / critical function?>` |
| Data class handled | `P0 / P1 / P2 / P3` |
| Retrieva record | `<link to the evaluation in Retrieva once created>` |

## 1. Need-first (gate: `cloud-adoption.md`)
One line — *we need this **because** …* (the gap that exists **today**; if you can't name it, stop).

## 2. Adopt-vs-build verdict (gate: `architecture-strategy.md`)
`adopt` · `build` · `extend an existing tool` — + one line why. (If **build**, go to `tech-stack-selection.md`.)

## 3. Shortlist — hard constraints (screen the longlist to 2–3)
A candidate that fails a hard constraint is **out**, regardless of features.

- [ ] Self-hostable / EU-sovereign (or a justified, gated exception — `cloud-adoption.md`)
- [ ] Licence acceptable (FOSS preferred; flag AGPL/commercial/ re-licensing risk)
- [ ] Can be SSO-gated via Authentik (OIDC or forward-auth)
- [ ] No hard dependency the platform can't satisfy

Shortlisted candidates: `<A>`, `<B>`, `<C>`.

## 4. Weighted score
Score each candidate **0–5** per criterion; `weighted = weight × score`; re-weight the defaults per eval
(weights should sum to ~100). Highest total wins — but a hard-constraint fail (§3) or a security blocker
(§6) overrides the score.

| Criterion | Weight | `<A>` | `<B>` | `<C>` | Notes |
|---|---:|---:|---:|---:|---|
| Need-fit / business fit | 15 | | | | |
| Self-hostable / sovereignty | 15 | | | | |
| FOSS / licence posture | 10 | | | | |
| SSO-able (Authentik) | 10 | | | | |
| Golden-path fit (Vault/ESO · GitOps · NetworkPolicy) | 12 | | | | |
| Observability hooks (Prom/Loki/OTel) | 8 | | | | |
| DORA class + data-class fit | 10 | | | | |
| Exit / portability (one-command leave) | 10 | | | | |
| Operational TCO (footprint vs quotas · solo maintenance) | 10 | | | | |
| **Weighted total** | **100** | | | | |

## 5. PoC on the dev cluster (not a vendor demo)
Deploy the frontrunner on **dev** with real Authentik SSO / Vault secrets / NetworkPolicies. Record what
actually happened (commands + results — `documentation.md` verified-reality rule).

- Deploy method (wrapper chart? vendor chart? raw?): `…`
- SSO wired (OIDC/forward-auth) + result: `…`
- Secrets via ESO/Vault + result: `…`
- NetworkPolicy / egress posture + result: `…`
- Observability (metrics/logs scraped?): `…`
- Verdict: `fits the golden path / needs adaptation / fights it`

## 6. Security / compliance review (gate: `bmad-compliance.md` + `observability/21-security-evaluation`)
**Mandatory for P0–P3 data or a trust-boundary-crossing tool.** SEC/SA sign-off.

- [ ] Threat surface reviewed (authn/authz, egress, secret handling, PII flow)
- [ ] Data classification handling acceptable for its P-class
- [ ] DORA third-party-ICT obligations identified (Art. 28/30 — captured in Retrieva)
- [ ] Supply chain (image provenance / SBOM / CVEs) acceptable
- Reviewer + verdict: `<SEC/SA, PASS / CONCERNS / FAIL>`

## 7. Decision
- **Selected:** `<candidate>` — **because** `<one line tying to the score + constraints>`
- **ADR:** `<link to the committed ADR: Context · Options · Trade-offs · Decision · Consequences>`
- **RACI:** `<who approved — project-governance.md>`
- **Exit test:** `<the one command / steps to remove it with no impact on the rest of the platform>`
- **Re-evaluation trigger(s):** `<licence change / EOL / CVE / DORA re-assessment / need disappears>`
