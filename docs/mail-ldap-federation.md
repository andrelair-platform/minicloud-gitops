# ADR — Unified credential: federate Stalwart mail auth to Authentik (LDAP)

- **Status:** ✅ **ACCEPTED & IMPLEMENTED (B1 + B2 live, 2026-10-07).** Mail now authenticates against
  Authentik; one credential for SSO + mail.
- **Owner:** SA/TL + SEC · **Created:** 2026-10-06 · **Cutover:** 2026-10-07 · **Tracks:** minicloud-gitops#1686
- **Relates to:** `workplace-architecture.md` (identity = perimeter), `twelve-factor.md` (#3 config),
  ktayl-iam #73/#74 (one-credential onboarding), memory `project_mail_authentik_ldap_federation`.
- **Operate/verify runbook + ops script:** `minicloud-ops/scripts/stalwart/stalwart-mail-ops.sh`.

## Context
A new employee used to end up with **two credentials**: an Authentik identity (SSO) and a **separate**
Stalwart mailbox password. That contradicts the workplace principle (one identity, identity is the
perimeter) and confuses users. Goal: **one credential, owned by Authentik** — the employee logs into SSO
and mail with the same password and rotates it once in Authentik.

## Decision
Federate Stalwart mail authentication to **Authentik via an LDAP outpost**, and switch Stalwart's active
authentication directory to it.

- **Onboarding (ktayl-iam #73/#74):** the Joiner sets the employee's **Authentik** password (+ mailbox)
  to a shared default, once, via a **scoped elevated token** (`reset_user_password` only).
- **B1 — Authentik LDAP outpost (GitOps):** `manifests/authentik-ldap-outpost/` — Deployment
  (`ghcr.io/goauthentik/ldap:2026.5.3`, non-root/readOnlyRootFS/drop-ALL) + Service `:3389/:6636` +
  outpost token via ESO + a `mail→outpost` NetworkPolicy. Provider `ktayl-ldap`, base DN `dc=devandre,dc=sbs`.
- **B2 — cutover (done):** Stalwart webadmin → **Settings → Authentication → Authentication Directory** =
  the LDAP directory. Mail login becomes the Authentik credential; the separate mailbox password disappears.

## Architecture (as-built)
```
employee ── SSO ─────────────▶ Authentik  (identity source of truth)
   │                                ▲   ▲
   │ IMAP/SMTP (password)           │   │ LDAP search (svc, superuser) + bind-as-user (:3389)
   ▼                                │   │
Nextcloud Mail ── IMAP/SMTP ─▶ Stalwart ─┘  (Authentication Directory = ktayl-ldap outpost)
```
- **Stalwart directory config:** `Use Bind Authentication = ON` (Authentik exposes **no** password hash →
  Stalwart searches by the login filter, then **binds as the user**). The Create-Directory **default
  filters work as-is** with Authentik (its LDAP entries carry `inetOrgPerson` for users and `groupOfNames`
  for groups).
- **Search service account:** `cn=stalwart-ldap-svc,ou=users,dc=devandre,dc=sbs` — made a **superuser**
  (this Authentik version has no `search_group` field, so a bound account can only list all users if it is
  a superuser). Bind creds in Vault `secret/platform/authentik-ldap-outpost` (`stalwart-bind-dn`/`-secret`).

## Key finding — mailbox keying (why the cutover is non-destructive)
The feared risk was that Stalwart might key mailboxes by the LDAP `cn` (= **matricule**, e.g. `100001`)
while the existing mailboxes are named by **email local-part** (`kanmegnea`) → a global switch could
orphan every mailbox. **Proven false by a controlled test:** a marker message placed in the internal
`testbox` mailbox (LDAP `cn=100099`, mail `testbox@`) **survived** the flip (login as `testbox@` via LDAP
still showed it). **→ Stalwart keys mailboxes by EMAIL and reuses the existing one.** Confirmed live:
`kanmegnea` kept all **7362** messages. No credential-alignment pre-step was needed.

## Special cases (as-built)
- **sophie.bernard (a new person):** `sophie.bernard` = a **user** (matricule `100006`, Direction RH).
  A brand-new LDAP user has **no Stalwart mailbox until their first mail delivery** (the box auto-creates
  on delivery); then login works.
- **it@ (IT team shared mailbox):** a **login-capable shared account** `it` (mail `it@devandre.sbs`; was a
  service account, converted to a normal account + shared password in Vault `secret/platform/stalwart-shared-it`).
  Stalwart exposes **no shared/other-users IMAP namespace** here, so **ACL delegation (SETACL) is set but
  not reachable** from another user's session → the working model is adding `it@` as a **second account in
  each IT-roster member's Nextcloud Mail** (reply-as it@ is native). Reusable: `stalwart-mail-ops.sh
  share-it <nc-uid>`. The group **Direction IT / SI** is the roster (ACL source), not a distribution list.
- **Distribution list vs shared mailbox:** Stalwart principal type `group` = shared mailbox (members share
  its box); `list` = fan-out. Authentik exposes a group's custom `mail` attribute over LDAP **with no
  property mapping** (so a pure distribution list would also work if ever needed).

## Security review (SEC)
- **Scoped privilege:** the onboarding token = a dedicated Authentik service account, Role granting **only**
  `authentik_core.reset_user_password`. Vault-stored, ESO-delivered, break-glass-provisioned
  (`minicloud-ops/scripts/authentik/provision-iam-credential.sh`). The ktayl-iam **sync** token stays least-privilege.
- **Recovery hatch preserved:** Stalwart's `STALWART_RECOVERY_ADMIN` (fallback admin) bypasses the directory
  → admin access survives an LDAP misconfig. **Revert = clear the `Authentication Directory` field** (back to
  internal) — captured before the flip.
- **Network:** NetworkPolicy allows **only** `mail` → the LDAP outpost `:3389/:6636`; egress-open ns reaches
  authentik-server implicitly.
- **No XOAUTH2:** Nextcloud Mail can't do custom-OIDC XOAUTH2 → mail stays **password-auth** against LDAP.
  On rotation in Authentik, the password stored in Nextcloud Mail goes stale → re-entered once. Accepted.
- **Shared `it@` secret:** a shared password (no per-user audit on `it@` itself) — accepted for a small team;
  per-user audit still exists on each member's own SSO login. Stored in Vault.

## Consequences
- **One credential** (Authentik) for SSO + mail; rotation in Authentik propagates to mail auth.
- The cutover was **non-destructive** (keying by email) and **reversible** (one field).
- Outpost + manifests are **GitOps-tracked** (not Authentik auto-deployed) — consistent with everything-in-gitops.

## Gotchas (learned — don't relearn)
1. **Stalwart caches auth/directory results.** A login attempted **before** the user's password is set gets
   cached as a failure and keeps failing until the cache clears. **Fix:** `stalwart-mail-ops.sh clear-cache`
   (restart Stalwart). This blocked `sophie.bernard` until cleared.
2. **New LDAP user ⇒ no mailbox until first delivery** — send a welcome mail (`stalwart-mail-ops.sh welcome`)
   to materialise it before expecting login.
3. **Stalwart mgmt REST API (`/api/settings`, `/api/principal`) is not reachable** here (404), the OAuth
   token endpoint rejects ROPC, and only `/api/account/*` (self) answers Basic auth → directory/principal
   changes are **webadmin-only**; mailbox ops are scriptable via **IMAP/JMAP** from an in-cluster pod.
4. **`Use Bind Authentication` MUST be ON** — Authentik exposes no password hash; OFF → all logins fail.

## Operate / verify (real commands, run live)
```bash
# verify a user authenticates via Authentik (IMAP 143 STARTTLS, run from a mail-ns pod):
ssh controller "bash ~/minicloud-ops/scripts/stalwart/stalwart-mail-ops.sh verify <email> [password]"
# materialise a new joiner's mailbox:   ... welcome <email>
# clear a stale auth cache:              ... clear-cache
# add the it@ shared mailbox to an IT member's Nextcloud Mail:  ... share-it <nc-user-id>
```
Final verification 2026-10-07 (4/4 PASS): `testbox` GONE · `kanmegnea` INBOX=7362 · `sophie` INBOX=1 ·
`it@` INBOX=5 — all three real accounts log in **via Authentik**.

## Rollback
Clear the Stalwart **Authentication Directory** field (→ internal auth; captured pre-change). The recovery
admin guarantees access meanwhile. Remove `manifests/authentik-ldap-outpost/` + the Authentik LDAP objects
to abandon. The ktayl-iam onboarding code is inert without its env (gated).
