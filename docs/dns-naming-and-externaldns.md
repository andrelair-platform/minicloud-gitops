# ADR: DNS naming convention + ExternalDNS automation

**Status:** Accepted (2026-09-18) · **Owner:** SA/TL · **Scope:** IS Foundations (ktayl-solution IS)
· **Layer:** organisational IS (NOT Retrieva — see the two-layer model in `.claude/rules/github-projects.md`)

## Context

Our DNS worked but had no *convention* and no *automation*:

- **Two access planes exist** — public `*.devandre.sbs` via **Cloudflare Tunnel** (+ Cloudflare
  WAF/CDN + Authentik SSO), and internal `*.10.0.0.200.nip.io` reachable only over **Tailscale**
  (+ minicloud CA). Kubernetes-internal is `*.svc.cluster.local`. Conceptually this is the
  enterprise *Internet / corp-private / cluster* three-plane model.
- **But naming was flat and inconsistent** — `grafana.devandre.sbs`, `argocd.devandre.sbs` sit as
  bare subdomains next to the owner's **portfolio** at `www.devandre.sbs` / apex `devandre.sbs`;
  environment suffixes were mixed (`retrieva-dev...`, `ktayl-policy-prod...`, plain `ktayl-policy...`).
- **DNS was semi-manual** — public records are created by hand (`cloudflared tunnel route dns` /
  the Cloudflare API); the zone is **not** in Terraform. No ExternalDNS.

This ADR fixes the two operational-maturity gaps: **one naming convention** and **DNS-as-part-of-GitOps**.

### Hard constraints
- **`devandre.sbs` apex + `www.devandre.sbs` are the owner's personal portfolio** — they must never be
  touched by org automation.
- **Retrieva** (the RNCP cert product) keeps its **own** domain `retrieva.online` — two-layer model,
  stays separate from the IS.
- Public exposure rides the **Cloudflare Tunnel** (id `bf5117ec-5986-47f0-a3ce-b96ab8854d21`), not a
  public LoadBalancer IP → public records are **CNAMEs to `<tunnel-id>.cfargotunnel.com`**, DNS-only
  (grey cloud), and each hostname needs a `cloudflared` ingress rule (origin `https://10.0.0.200`,
  `originServerName` = the internal name).

## Decision 1 — the naming convention

The organisation (**ktayl-solution IS**) gets a dedicated namespace **under** `devandre.sbs` so it never
collides with the portfolio: **`ktayl.devandre.sbs`**. One enterprise-wide convention, four planes:

| Plane | Convention | Reached via | Examples |
|---|---|---|---|
| **Personal (not org)** | `devandre.sbs`, `www.devandre.sbs` | Cloudflare | the owner's portfolio — **off-limits to org automation** |
| **Retrieva (cert product)** | `retrieva.online` (own domain) | Cloudflare | `retrieva.online` — separate layer |
| **Public — org** | `<app>.ktayl.devandre.sbs` (prod) · `<app>.<env>.ktayl.devandre.sbs` (non-prod) | Cloudflare Tunnel + WAF + **Authentik SSO** | `www.ktayl.devandre.sbs`, `broker.ktayl.devandre.sbs`, `api.ktayl.devandre.sbs`, `broker.dev.ktayl.devandre.sbs` |
| **Corp — internal business apps** | `<app>.10.0.0.200.nip.io` (today) → target `<app>.corp.ktayl.devandre.sbs` | **Tailscale only** + minicloud CA | `underwriting.10.0.0.200.nip.io`, `glpi.10.0.0.200.nip.io` |
| **Platform — ops tooling** | `<tool>.10.0.0.200.nip.io` (**Tailscale-only, preferred**) → optional `<tool>.platform.ktayl.devandre.sbs` behind SSO | Tailscale (default) | `argocd`, `grafana`, `vault`, `harbor`, `kargo` |
| **Kubernetes-internal** | `<svc>.<ns>.svc.cluster.local` | in-cluster only | `stalwart.mail.svc.cluster.local` |

**Rules that make it *one* convention:**
1. **Environment = a subdomain *prefix*, prod = the clean name.** `broker.dev.ktayl.devandre.sbs`,
   `broker.test.ktayl.devandre.sbs`, `broker.ktayl.devandre.sbs` (prod). This **supersedes** the old
   suffix style (`broker-dev...`). nip.io supports multi-level labels, so the corp plane uses the same
   shape: `underwriting.dev.10.0.0.200.nip.io`.
2. **Microservices are NOT hostnames.** Internal services stay on `svc.cluster.local` behind
   default-deny egress NetworkPolicies; only a genuine external/entry surface (an app UI, an API
   gateway) earns a public/corp hostname. (Already our practice — codified here.)
3. **Platform/ops tooling defaults to Tailscale-only.** Do not add a public `*.devandre.sbs` record
   for argocd/grafana/vault/etc. unless there's a stated need; identity-as-perimeter (Authentik SSO +
   MFA) is the control if one is ever exposed. See *Decision 3*.
4. **Personal vs org is a hard boundary.** Org hostnames live under `ktayl.devandre.sbs`; the portfolio
   keeps `www`/apex. Automation (below) is domain-filtered so it *cannot* cross that boundary.

## Decision 2 — ExternalDNS (Cloudflare provider), opt-in + fail-safe

Deploy **ExternalDNS** (chart `external-dns` 1.22.0, ns `external-dns`) so an org app's Ingress
**creates its own DNS record** — the GitOps `Ingress → DNS` flow. Because our public plane is
tunnel-based, ExternalDNS publishes a **CNAME to the tunnel**, not an A-record. It is configured to be
impossible-to-misfire:

| Guard | Value | Why |
|---|---|---|
| `--domain-filter` | `ktayl.devandre.sbs` | can only ever touch the org namespace — never the portfolio, never `retrieva.online`, never the existing flat `*.devandre.sbs` |
| `policy` | **`upsert-only`** | **never deletes** a record — worst case is an extra record, never a removal |
| `--label-filter` | `external-dns=enabled` | **opt-in**: only Ingresses explicitly labelled are managed; every existing Ingress is ignored → zero blast radius on deploy |
| `registry` / `txtOwnerId` | `txt` / `minicloud-externaldns` | ownership TXT records so it only manages what it created |
| `--cloudflare-proxied` | `false` | tunnel CNAMEs must be **DNS-only** (grey cloud) |
| provider token | Vault `secret/platform/cloudflare` `api-token` via ESO → `cloudflare-api-token` | (least-privilege dedicated token = a future improvement; noted below) |

**How an org app opts in** (the scaffold will carry this):
```yaml
# Ingress metadata for a public org app
metadata:
  labels:
    external-dns: enabled                                   # opt into ExternalDNS
  annotations:
    external-dns.alpha.kubernetes.io/target: "bf5117ec-5986-47f0-a3ce-b96ab8854d21.cfargotunnel.com"
    external-dns.alpha.kubernetes.io/cloudflare-proxied: "false"
spec:
  rules:
    - host: broker.ktayl.devandre.sbs                       # the public org name
```
On sync, ExternalDNS creates `broker.ktayl.devandre.sbs CNAME <tunnel>.cfargotunnel.com` (DNS-only) +
its ownership TXT. **On first deploy it manages nothing** (no Ingress is labelled yet) — it is installed,
scoped, and ready; records appear as apps adopt the convention.

### The companion piece — the tunnel ingress rule (NOT automated by ExternalDNS)
ExternalDNS creates the **DNS record**; it does **not** create the `cloudflared` ingress rule that maps
the hostname to `https://10.0.0.200`. Two ways to close that gap for the org plane:
- **Preferred (zero-touch):** add ONE **wildcard** rule to the controller's `~/.cloudflared/config.yml`
  — `- hostname: "*.ktayl.devandre.sbs" → service: https://10.0.0.200` with Host-based routing on
  ingress-nginx (the org Ingress host = the public name, so no `originServerName` rewrite needed) — plus
  a **wildcard TLS cert** `*.ktayl.devandre.sbs`. Then a new org app needs only its Ingress
  (label + host); DNS + routing are automatic. *(Controller-side + cert = a follow-up step, tracked
  separately — cloudflared runs as systemd on the controller, outside GitOps.)*
- **Interim (per-host):** keep adding a per-host `cloudflared` rule as today, while ExternalDNS handles
  the record. Removes half the manual work immediately.

## Decision 3 — platform tooling defaults to Tailscale-only (security posture)

The enterprise model keeps ops tooling on private DNS. We currently expose `argocd`/`grafana`/`vault`/…
publicly on `*.devandre.sbs` (behind Authentik SSO) for solo-operator convenience. **Going forward the
default is Tailscale-only** (`*.10.0.0.200.nip.io`); a public record for a platform tool requires a
stated need. Existing public platform records may be retired opportunistically (drop the `cloudflared`
rule + the DNS record) to shrink attack surface. Non-blocking; tracked as a follow-up.

## Migration (phased — no rip-and-replace)

The existing ~40 hostnames are **not** renamed in a big bang (that would churn certs, Authentik redirect
URIs, tunnel rules, and Ingress hosts). Instead:
1. **New org apps** use `*.ktayl.devandre.sbs` + the ExternalDNS opt-in from day one.
2. **The scaffold** (`services/_template-helm`) ships the convention + the opt-in labels/annotations.
3. **Existing apps** migrate opportunistically when they're next touched (or move to Tailscale-only per
   Decision 3). The portfolio (`www`/apex) and `retrieva.online` are never touched.

## Consequences

- **Positive:** one documented convention (fixes the inconsistency); DNS becomes part of GitOps for org
  apps; the portfolio/org boundary is enforced by tooling, not discipline; smaller public attack surface
  over time; closer to a mature enterprise platform (the reviewer/interview story).
- **Cost/risk:** ExternalDNS is a new controller with DNS write access — mitigated to near-zero by
  `upsert-only` + `--domain-filter` + label opt-in (see the guard table). Full zero-touch public
  onboarding still needs the wildcard tunnel rule + wildcard cert (follow-up).
- **Deliberately NOT done (need-first, `.claude/rules/cloud-adoption.md`):** no private DNS-zone server /
  split-horizon (`corp.ktayl.devandre.sbs` stays as a *target*, nip.io+Tailscale meets the need today);
  no Gateway API migration (ingress-nginx is fine); no Terraform-managed DNS zone yet (ExternalDNS covers
  the app-record flow; zone-as-code is a later step).
- **Least-privilege token** (dedicated Cloudflare token scoped to `devandre.sbs` Zone:Read + DNS:Edit,
  vs reusing the platform token) is a recommended hardening follow-up.

## References
- Access/PKI: `.claude/rules/connectivity.md` · Tunnel/DNS ops: `.claude/rules/ops-runbooks.md`
  (*Cloudflare*) · Deploy golden path: `.claude/rules/gitops.md` · URLs: `.claude/rules/urls.md`.
- Two-layer model (IS vs Retrieva): `.claude/rules/github-projects.md`.
- Mail-auth posture on the same zone (custom MAIL FROM, also Cloudflare-managed): docs
  `developer-platform/amazon-ses`.
