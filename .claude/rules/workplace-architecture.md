# Workplace Architecture — browser-first, data-server-side, identity-enforced (BYOD)

The **constitution for the digital workplace** (Digital Workplace #10) and, by extension, every
app an employee touches. It is the *positive build principle* that pairs with the *scope decision*
in `project-governance.md` → *BYOD — no managed physical endpoints* (that says what's out of scope;
this says how every app must therefore be built). Every new user-facing app inherits this.

## The principle (goes in the EA blueprint verbatim)

> **The enterprise operates a browser-first BYOD workplace. Employee endpoints are considered
> UNTRUSTED and are not centrally managed. Security is therefore enforced primarily at the identity,
> session, application, API and data layers. Corporate information should remain server-side whenever
> possible, with web-based collaboration preferred over local synchronization or storage. Strong
> authentication, fine-grained authorization, auditability, data classification and restricted
> handling of sensitive information are foundational architectural requirements.**

Consequence: `DEVICE = UNTRUSTED` → **identity is the security perimeter.** The control chain is
`never-trust-device → authenticate → MFA → authorize app → authorize resource → limit session →
audit`. There is **no** reliance on MDM/endpoint trust (see the out-of-scope list).

## Requirements every user-facing app MUST satisfy (admission to the workplace)
1. **SSO via Authentik only** — no app-local passwords/user store. OIDC/SAML natively, or the
   **Authentik proxy/forward-auth** provider for apps that don't (reference: the claims-workbench
   forward-auth wiring, [[feedback_public_sso_app_forwardauth]]).
2. **Group-gated authorization, never "any authenticated user"** — bind the app to the right
   Authentik group(s) (`Direction <Dept>` / `Platform Admins` …); membership lifecycle is governed
   by `ktayl-iam` (request → dual-approval → provision). ABAC (attribute checks: country / LoB) is
   layered on for cross-border domains (International Programs).
3. **Session controls sized to sensitivity** — MFA; session + token lifetime; idle timeout;
   **re-authentication for privileged actions**. Sensitive apps get short sessions + step-up. Prefer
   **passkey / WebAuthn** over password+TOTP where possible (anti-phishing on BYOD).
4. **Data stays server-side** — prefer **in-browser** view/edit (OnlyOffice/Collabora in Nextcloud,
   web UIs) over download-and-open-locally. For **RESTRICTED** data: web-only, no public/anonymous
   share, no local sync, watermark where feasible.
5. **Honour data classification** — INTERNAL (download ok) · CONFIDENTIAL (browser-preferred,
   download-restricted) · RESTRICTED (web-only, short session, strong MFA, audit). Maps onto the
   existing P0–P3 data classes; apply it to file/document handling (Nextcloud hardening), not just AI.
6. **Auditable via the Authentik identity** — every action reconstructable to
   **who · when · from where · which app · what action · which resource**. Mandatory for a regulated
   insurer (DORA/GDPR).
7. **Default-deny egress + private datastores** — users only ever reach `<app>.devandre.sbs`; never
   Postgres/Redis/NATS/MinIO/Vault/k8s-API/monitoring. Governed-egress netpols (DLP: Presidio at the
   AI gateway; extend to data surfaces).
8. **No device-trust assumptions** — no MDM/agent/remote-wipe in the control path (see below).

## Two workforce tiers (the standard vs the sensitive)
- **Standard workforce** — BYOD browser + Authentik MFA + web apps. (Today's default.)
- **Sensitive workforce** (finance payment approval, legal/M&A, sanctions, exec docs) — add
  **browser isolation / a virtual workspace** so the personal device receives only pixels/keyboard/
  mouse and data never lands locally. *Future — add when the sensitive surface is real.*

## Stack (Authentik-centered — fit-for-purpose, already deployed)
Identity **Authentik** · Mail **Stalwart** · Files/Groupware **Nextcloud** · Office **OnlyOffice** ·
Chat **Matrix/Element** · Meetings **Jitsi** · Projects **Plane** · Workflow **Temporal + n8n** ·
AI **Open WebUI / LiteLLM / Langfuse** · Secrets **Vault** · Runtime-sec **Falco** · Logs **Loki** ·
Obs **Prometheus/Grafana/OTel** · Object **MinIO** · DB **Postgres/CNPG** · Ingress **nginx** ·
Certs **cert-manager** · k8s **k3s**. (These are the fit-for-purpose equivalents of the reference
design — e.g. OnlyOffice≈Collabora, Plane≈OpenProject, Temporal≈Camunda, Falco≈Wazuh.)

## Explicitly OUT of scope (the BYOD consequence — do NOT build/propose these)
Intune · Fleet/osquery · GLPI-Agent/MDM · device enrollment · corporate imaging · remote wipe ·
endpoint config management. Accepted residual risk (screenshot / local copy / personal malware) is
documented in `project-governance.md` BYOD with its revisit trigger — mitigated by keeping data
server-side + the sensitive tier, not by managing the device.

Related: `project-governance.md` (BYOD scope decision), [[project_iam_custom_access_governance]],
[[feedback_public_sso_app_forwardauth]], [[feedback_homer_static_rbac_two_portals]].
