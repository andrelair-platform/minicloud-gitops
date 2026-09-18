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
  public LoadBalancer IP → public records are **proxied CNAMEs to `<tunnel-id>.cfargotunnel.com`**
  (orange cloud — the edge connects to the tunnel; a DNS-only record would not route), and each hostname
  needs a `cloudflared` ingress rule (origin `https://10.0.0.200`,
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
| `--domain-filter` | `ktayl.devandre.sbs` | **this is the opt-in.** Can only ever touch the org namespace — never the portfolio, never `retrieva.online`, never the existing flat `*.devandre.sbs`. An app is managed only when its Ingress host is under this zone, which is a deliberate act (internal apps use nip.io). Verified: **no existing Ingress uses a `ktayl.devandre.sbs` host** → idle on deploy. |
| `policy` | **`upsert-only`** | **never deletes** a record — worst case is an extra record, never a removal |
| target annotation | `external-dns.alpha.kubernetes.io/target: <tunnel>.cfargotunnel.com` | required per-record so the record is a **CNAME to the tunnel**, not an A-record to the private MetalLB IP |
| `registry` / `txtOwnerId` | `txt` / `minicloud-externaldns` | ownership TXT records so it only manages what it created |
| `--cloudflare-proxied` | **`true`** (global) | tunnel CNAMEs **must be proxied** (orange cloud) — the edge connects to the tunnel; a DNS-only record would not route |
| provider token | Vault `secret/platform/cloudflare` `api-token` (the broad `MINICLOUD` token) via ESO → `cloudflare-api-token` | **accepted risk** — the token is account-wide, but ExternalDNS's *own* blast radius is already capped by `--domain-filter` + `upsert-only` regardless of token scope. A dedicated scoped token is defense-in-depth (see *Consequences*). |

> **Why no `--label-filter`?** An earlier design used a `external-dns=enabled` label as an extra opt-in,
> but the shared **`minicloud-app-deployment` library ingress emits only the standard `app.labels`** (no
> hook for a custom label) and the library can't be republished from here (read-only ghcr token). Since
> `--domain-filter` + the deliberate `ktayl.devandre.sbs` host is already an explicit, verified-safe
> opt-in, the label adds no safety worth a library change. Both the host and the target annotation are
> set through the **library ingress values** the scaffold already exposes (`ingress.host` +
> `ingress.annotations`) — no custom template needed.

**How an org app opts in** (the scaffold carries this — see `services/_template-helm/helm/values-prod.yaml`):
```yaml
# wrapper-chart values (library ingress) for a public org app
minicloud-app-deployment:
  ingress:
    host: broker.ktayl.devandre.sbs                          # the org name = the opt-in
    annotations:
      external-dns.alpha.kubernetes.io/target: "bf5117ec-5986-47f0-a3ce-b96ab8854d21.cfargotunnel.com"
      # proxied defaults to true globally (tunnel CNAMEs must be proxied) — no per-record override
  certificate:
    dnsNames: [broker.ktayl.devandre.sbs]
```
On sync, ExternalDNS creates `broker.ktayl.devandre.sbs CNAME <tunnel>.cfargotunnel.com` (proxied) +
its ownership TXT. **On first deploy it manages nothing** (no Ingress uses a `ktayl.devandre.sbs` host
yet) — installed, scoped, and ready; records appear as apps adopt the convention.

### The companion piece — tunnel rule + edge cert (DEFERRED to the first public org app)
ExternalDNS creates the **DNS record**; it does **not** create the `cloudflared` ingress rule, and it
cannot conjure the **Cloudflare edge TLS certificate**. Two gaps remain for a fully public org app, both
**deliberately deferred** (2026-09-18) because **no public org app exists yet**:

1. **Tunnel routing (cheap, controller-side).** Add ONE **wildcard** rule to `~/.cloudflared/config.yml`
   — `- hostname: "*.ktayl.devandre.sbs" → service: https://10.0.0.200` (Host-based routing to
   ingress-nginx) — plus an internal wildcard cert `*.ktayl.devandre.sbs` from ClusterIssuer
   `minicloud-ca` for the cloudflared↔ingress-nginx leg (`noTLSVerify` anyway). Free. *(Interim: a
   per-host `cloudflared` rule as today; ExternalDNS still makes the record.)*
2. **Edge TLS (the real blocker — NOT free).** `*.ktayl.devandre.sbs` is a **two-level** subdomain.
   Cloudflare's free **Universal SSL covers `devandre.sbs` + `*.devandre.sbs` (one level only)** — a
   browser hitting `broker.ktayl.devandre.sbs` gets an edge TLS error unless we either buy **Advanced
   Certificate Manager (~$10/mo)** or adopt a **one-level** org name (e.g. `ktayl-<app>.devandre.sbs`).
   The first public org app resolves this (apply the `cloud-adoption.md` need-first gate then).

## Decision 3 — three access tiers (Tailscale vs public+SSO), by *who needs it*

The access decision is **not** "internal vs external" — every public app is already SSO-gated. It is
*who* needs to reach it and *from where*. **Tailscale** is a private mesh (enrolled devices, any
network); **public+Cloudflare** is any browser, gated by **Authentik SSO + MFA**. Because the org is
**BYOD / browser-first** (`project-governance.md` — no managed endpoints), forcing employees onto
Tailscale for daily apps would fight that model. So three tiers:

| Tier | Reached by | Apps | Rationale |
|---|---|---|---|
| **① Tailscale-only** | operator/admins (enrolled devices) | argocd, vault, grafana, harbor, backstage, temporal, nats, litellm, langfuse, flowise, homer | control-plane/infra — **no employee ever needs these**; public = pure attack surface. Reachable via `*.10.0.0.200.nip.io` over Tailscale only. |
| **② Public + SSO** | employees, any device (BYOD) | chat, mail, cloud, erp, plane, n8n, onlyoffice, meet, vault-pw, matrix, element | daily business apps — browser-first over Cloudflare Tunnel + Authentik SSO + MFA. |
| **③ Public, external-facing** | anyone outside the org | demo, auth (IdP), retrieva.online, sign (external signers) | must reach people outside the org. |

**Rule:** an infra tool (tier ①) is **not** added to the tunnel config without a stated reason —
identity-as-perimeter (SSO+MFA) is the control if one ever is. `controller.devandre.sbs` (SSH) stays
public as the **break-glass** (recover when Tailscale is down). Applied 2026-09-18: tier ① removed from
the public tunnel config (they keep their nip.io/Tailscale door — verified reachable first); the dead
`intranet`/`wiki`/`dev.*` routes were cleaned up (they backed no service — intranet ≈ Homer/Nextcloud
Dashboard, wiki ≈ Nextcloud Collectives/Backstage TechDocs).

## Migration (phased — no rip-and-replace)

The existing ~40 hostnames are **not** renamed in a big bang (that would churn certs, Authentik redirect
URIs, tunnel rules, and Ingress hosts). Instead:
1. **New org apps** use `*.ktayl.devandre.sbs` + the ExternalDNS opt-in from day one.
2. **The scaffold** (`services/_template-helm`) ships the convention + the opt-in (host + target annotation).
3. **Existing apps** migrate opportunistically when they're next touched (or move to Tailscale-only per
   Decision 3). The portfolio (`www`/apex) and `retrieva.online` are never touched.

## Consequences

- **Positive:** one documented convention (fixes the inconsistency); DNS becomes part of GitOps for org
  apps; the portfolio/org boundary is enforced by tooling, not discipline; smaller public attack surface
  over time; closer to a mature enterprise platform (the reviewer/interview story).
- **Cost/risk:** ExternalDNS is a new controller with DNS write access — mitigated to near-zero by
  `upsert-only` + `--domain-filter` (the hostname opt-in) + txt-ownership (see the guard table). Full zero-touch public
  onboarding still needs the wildcard tunnel rule + an **edge cert** — the latter isn't free for a 2-level
  subdomain (deferred to the first public org app; see *The companion piece*).
- **Deliberately NOT done (need-first, `.claude/rules/cloud-adoption.md`):** no private DNS-zone server /
  split-horizon (`corp.ktayl.devandre.sbs` stays as a *target*, nip.io+Tailscale meets the need today);
  no Gateway API migration (ingress-nginx is fine); no Terraform-managed DNS zone yet (ExternalDNS covers
  the app-record flow; zone-as-code is a later step).
- **Least-privilege token — accepted-risk (2026-09-18), scoped token = deferred defense-in-depth.**
  ExternalDNS uses the broad account-wide `MINICLOUD` token (Vault `platform/cloudflare` `api-token`) —
  the same one that runs the Tunnel + R2. **Why accepted:** ExternalDNS can only ever upsert records
  under `ktayl.devandre.sbs` (its `--domain-filter` + `upsert-only`), so the *live* blast radius is the
  same whether the token is broad or scoped. The scoped token only matters **if the ExternalDNS
  pod/secret were compromised** — then a `devandre.sbs`-only Zone:Read+DNS:Edit token would limit what a
  leaked credential could do (vs. the broad token = all DNS + R2 + Tunnel). Minting it needs a
  **dashboard** step (the broad token lacks User→API-Tokens permission, so it can't self-mint) → store
  at `secret/platform/cloudflare-externaldns` + repoint the `cloudflare-api-token` ES. Deferred as
  hardening, not a live gap.

## References
- Access/PKI: `.claude/rules/connectivity.md` · Tunnel/DNS ops: `.claude/rules/ops-runbooks.md`
  (*Cloudflare*) · Deploy golden path: `.claude/rules/gitops.md` · URLs: `.claude/rules/urls.md`.
- Two-layer model (IS vs Retrieva): `.claude/rules/github-projects.md`.
- Mail-auth posture on the same zone (custom MAIL FROM, also Cloudflare-managed): docs
  `developer-platform/amazon-ses`.
