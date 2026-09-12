# ADR: Two-layer identity — self-hosted workforce IdP + managed customer IdP

**Status:** Accepted · **Date:** 2026-09-12 · **Board:** GitOps — Platform Engineering (#3)

## Context
The platform authenticates ~30 internal tools (ArgoCD, Grafana, Vault, Harbor, Backstage, Plane,
ERPNext, Open WebUI, …) through **Authentik**, self-hosted on the k3s cluster (OIDC + ingress-nginx
forward-auth; login `kanmegnea` + TOTP). The question was raised: *should we replace Authentik with
Microsoft Entra ID* (the IdP used at HDI and most enterprises)?

"Replace" is the wrong framing. Workforce SSO and customer identity are two different problems, and
the platform's sovereignty/availability/cost constraints make the *core* IdP choice non-obvious.

## Decision
**Adopt a two-layer identity model; do not replace Authentik.**

1. **Workforce / platform IdP = Authentik (self-hosted).** All staff + internal-tool SSO stays on
   Authentik on the cluster. The **control plane** (ArgoCD, Vault, Grafana, Harbor, Backstage) **must
   not** depend on an external cloud IdP for login.
2. **Customer / external IdP = Microsoft Entra External ID** (free ≤50k MAU), introduced **when a
   customer-facing product needs it** (e.g. Retrieva SaaS users, a broker portal) — never for staff SSO.
3. **Enterprise-SSO credibility = federation**, not migration: Authentik may **federate to Entra as an
   upstream source** ("Login with Microsoft") to demonstrate enterprise SSO *without* making the
   platform depend on Entra.

## Alternatives considered
- **Entra ID as the sole/primary IdP (rejected).** Moves the platform's most foundational service into
  a US-jurisdiction managed SaaS → sovereignty loss, residency/CLOUD-Act exposure, a **bootstrap
  circular dependency** (you couldn't log into Vault/ArgoCD to fix an outage *caused by* losing
  external connectivity), and cost (workforce SSO + Conditional Access needs paid P1/P2, breaching the
  €10/mo/provider cap). It also contradicts the platform's own thesis (a sovereign, DORA-compliant IS).
- **Authentik only, forever (partial).** Correct for workforce, but leaves no credible customer-IAM or
  enterprise-SSO story for the SaaS/cert narrative.
- **Two-layer (chosen).** Keeps the sovereign core, adds the managed layer exactly where it fits, and
  *demonstrates* concentration-risk discipline instead of violating it.

## Consequences
- **Hard rule:** platform **control-plane auth stays on self-hosted Authentik** — never gate ArgoCD /
  Vault / Grafana / Harbor / Backstage behind an external cloud IdP (availability + bootstrap).
- A new **customer-facing** product provisions identity on **Entra External ID** (free tier; within the
  cloud-adoption €-cap + decision gate — see `.claude/rules/cloud-adoption.md`), separate from staff.
- **Federation** (Authentik ← Entra upstream) is the sanctioned way to show "enterprise login with
  Microsoft"; it adds a *source*, not a dependency.
- Skill coverage stays complementary: Authentik internals here (flows, outposts, LDAP, SCIM, property
  mappings) + managed Entra at HDI.

## Compliance mapping
- **DORA (Art. 28–29, concentration & exit):** splitting workforce vs customer identity across a
  self-hosted IdP and a managed one, with federation rather than lock-in, is deliberate
  concentration-risk management with a clear exit path — this ADR is evidence of it.
- **GDPR / residency:** staff identity + the control plane stay on-cluster (EU/sovereign); customer
  PII identity, if externalised, uses Entra External ID's EU data residency with a DPA.
- **EU AI Act:** n/a (identity infrastructure).

## Maintenance
Revisit only when a customer-facing product actually starts (then run the `cloud-adoption.md` gate for
the Entra External ID tenant), or if Authentik can no longer meet a workforce requirement. "Entra is
what enterprises use" is **not** grounds to move the sovereign core — that trade-off is decided here.
