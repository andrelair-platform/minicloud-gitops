# ADR — Unified credential: federate Stalwart mail auth to Authentik (LDAP)

- **Status:** Proposed — **governance gate (architecture + security review) pending owner approval.**
  The B2 cutover (switching Stalwart's auth to LDAP) MUST NOT be executed until this ADR is approved.
- **Owner:** SA/TL + SEC · **Date:** 2026-10-06 · **Tracks:** minicloud-gitops#1686
- **Relates to:** `workplace-architecture.md` (identity = perimeter), `twelve-factor.md` (#3 config),
  ktayl-iam #73/#74 (the one-credential onboarding code), `bmad-compliance.md` (this gate).

## Context
A new employee today ends up with **two credentials**: an Authentik identity (SSO) and a **separate**
Stalwart mailbox password. That contradicts the workplace principle (one identity, identity is the
perimeter) and confuses users. We want **one credential, owned by Authentik**, with mail authenticating
*against* Authentik — the employee logs into SSO and mail with the same password, and rotates it once
in Authentik.

## Decision
Federate Stalwart's mail authentication to **Authentik via an LDAP outpost**:
- **Onboarding (done, ktayl-iam #73/#74):** the Joiner sets the employee's **Authentik** password (+ the
  mailbox) to a shared default, once, via a **scoped elevated token** (`reset_user_password` only).
- **B1 (this ADR, additive):** deploy an **Authentik LDAP outpost** (GitOps-managed Deployment + Service
  `:3389/:6636` + the outpost token via ESO + a `mail→outpost` NetworkPolicy). Base DN `dc=devandre,dc=sbs`.
- **B2 (gated):** configure Stalwart with an **LDAP directory** pointing at the outpost and switch mail
  auth to it → the mail login becomes the Authentik credential; the separate mailbox password disappears.

## Architecture
```
employee ── SSO ─────────────▶ Authentik (identity source of truth)
   │                                 ▲   ▲
   │ IMAP/SMTP (password)            │   │ LDAP bind+search (:3389, scoped svc account)
   ▼                                 │   │
Nextcloud Mail ── IMAP/SMTP ─▶ Stalwart ─┘  (LDAP directory → validates against Authentik)
```

## Security review (SEC)
- **Scoped privilege (threat T4 preserved):** the onboarding token belongs to a dedicated Authentik
  service account with a Role granting **only** `authentik_core.reset_user_password` — not admin; the
  ktayl-iam **sync** token stays least-privilege. Token stored in Vault, delivered by ESO. Decrypted/
  provisioned via a break-glass script (`minicloud-ops/scripts/authentik/provision-iam-credential.sh`).
- **Mono-directory global-switch risk (the critical one):** Stalwart appears to use a **single active
  auth directory**. Switching to LDAP affects **all** mailboxes at once, not a test one — so B2 cannot be
  isolated to a throwaway account.
  - **Mitigation 1 — credential alignment before cutover:** set the owner's (and any existing user's)
    Authentik password = the value their mail client already stores, so the LDAP switch keeps their mail
    working (no lockout). For the owner: align Authentik `100001` → the password Nextcloud Mail stores.
  - **Mitigation 2 — recovery admin preserved:** Stalwart's `STALWART_RECOVERY_ADMIN` (fallback admin)
    bypasses the directory → admin access survives an LDAP misconfig (rollback hatch).
  - **Mitigation 3 — reversible:** B2 is a config change; capture the pre-change Stalwart auth config and
    the exact revert, and verify the owner's mail still syncs immediately after the switch. If anything is
    off, revert to internal auth.
  - **Precondition:** verify whether Stalwart can run **internal + LDAP in combination/fallback** (so the
    existing internal accounts survive) — if it cannot, B2 is a hard global cutover and only proceeds
    once every active mailbox's credential is aligned.
- **Network:** a NetworkPolicy allows **only** `mail` (Stalwart) → the LDAP outpost `:3389`; nothing else.
- **No XOAUTH2:** Nextcloud Mail can't do custom-OIDC XOAUTH2, so mail stays **password-auth** (against
  LDAP). Consequence: on password **rotation** in Authentik, the password stored in Nextcloud Mail goes
  stale → the user re-enters it once (or the future self-service rotation flow updates it). Accepted.

## Consequences
- One credential (Authentik) for SSO + mail; rotation in Authentik propagates to mail auth.
- B1 is additive and safe (no effect on existing mail). B2 is a **gated, reversible, credential-aligned**
  cutover — executed only after this ADR is approved, verified non-breaking on the owner's live mailbox.
- Outpost is a **GitOps-tracked workload** (not Authentik auto-deployed) — consistent with the platform's
  everything-in-gitops rule.

## Rollback
Revert the Stalwart LDAP directory config to the prior internal-auth config (captured pre-change); the
recovery admin guarantees access meanwhile. Remove the outpost manifest + the Authentik LDAP objects if
abandoning. The ktayl-iam onboarding code is inert without the env (already gated).
