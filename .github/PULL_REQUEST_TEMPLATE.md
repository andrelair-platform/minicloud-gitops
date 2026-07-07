## Change Description

<!-- What is changing and why? -->

## Change Classification

**Type:**
- [ ] `standard` — pre-approved routine change (config value update, image tag bump, dependency update)
- [ ] `normal` — requires review and approval (new workload, topology change, security policy update)
- [ ] `emergency` — urgent fix, expedited approval (active incident, critical vulnerability)

**Risk level:**
- [ ] `low` — isolated change, easy rollback, no user impact
- [ ] `medium` — affects multiple components or has brief user-visible impact
- [ ] `high` — platform-wide impact, extended rollback window, or touches security controls

**ACPR / DORA reference** *(optional — fill for compliance-relevant changes)*:
<!-- e.g. DORA Art.9 — ICT change management | ACPR 2021-R-01 §4.2 — cloud configuration changes -->

---

## Impact Assessment

**Affected namespaces / services:**

**Expected downtime:** none / brief (<60s) / planned window

---

## Rollback Plan

<!-- How do you undo this if something goes wrong? -->
<!-- e.g. git revert <sha> + ArgoCD selfHeal picks it up within 3 min -->

---

## Test Plan

<!-- What did you verify before opening this PR? -->
- [ ] `kustomize build` / Helm template renders without error
- [ ] Tested in dev overlay before promoting to staging/prod
- [ ] Regression check passes (or scoped check for affected components)

---

## Post-Change Verification

<!-- What will you check after merge to confirm the change is healthy? -->
- [ ] ArgoCD app Synced + Healthy
- [ ] Relevant pods Running / Ready
- [ ] No new Gatekeeper violations
