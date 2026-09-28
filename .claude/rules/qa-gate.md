# QA Gate — mandatory live dev-environment test pass before prod promotion

**Every custom-built app MUST pass an adversarial QA agent test against the LIVE dev deployment before it
is promoted to prod.** CI (testing.md L0–L4) proves the code in isolation with mocks; the QA gate proves
the **running service in the real dev environment** — it catches integration, deploy, runtime and config
bugs that unit/mocked tests structurally cannot. Green CI is **not** sufficient to promote.

## The gate (where it sits)
```
story built → CI L0–L4 green → Kargo promotes to DEV → ***QA GATE (this)*** → prod promotion PR (CODEOWNERS)
```
- Runs **after** the artifact is live on dev (real CNPG, real netpols, real Authentik/NATS, self-migration,
  the actual image — not a test harness).
- **Blockers gate promotion.** No Kargo/CODEOWNERS prod PR until the QA pass is clean (or every finding is
  triaged: fixed, or accepted+documented with an owner sign-off).
- Applies to **Path B/C** work (new product / feature / boundary-crossing). A Path-A one-liner/hotfix is
  exempt from a full pass but still gets a targeted smoke of the changed surface.

## Why it exists — the reference bug (ktayl-underwriting, 2026-09-28)
"Add request logging" passed CI and unit tests but emitted **zero logs live**: the app self-migrates on
startup and alembic's `fileConfig()` (default `disable_existing_loggers=True`) **disabled every logger**
after the startup migration. Mocked tests couldn't see it — only re-testing the **running container**
did. Same pass also caught an unauthenticated policy-binding API (B1), a hardcoded audit actor (B2), and a
bound file that wasn't locked (M1). None were visible from CI alone.

## What the QA agent MUST cover (adversarial, not happy-path)
1. **Happy paths** — every outcome branch (e.g. accept/refer/decline), not just one.
2. **Input validation** — bad/missing/oversized/wrong-type/enum inputs → **4xx, never 5xx**; unicode; huge strings.
3. **Not-found** — every endpoint on a missing id → 404.
4. **State & ordering guards** — out-of-order calls, operating on a terminal/locked entity (e.g. re-act on a
   bound/closed record → 409), acting on the wrong state.
5. **Idempotency** — safe retries (re-submit/re-bind), deterministic ids, no duplicate side-effects; check the
   DB for row duplication / unbounded growth.
6. **Boundary conditions** — exact thresholds (`<=` vs `<`, `>` vs `>=`), off-by-one, rounding (money =
   minor units, reconcile breakdowns to totals).
7. **Data integrity** — units/currency, append-only vs mutable semantics, cross-record consistency.
8. **Security / authz** — is the ingress/API actually authenticated? per-endpoint scope enforced (401/403)?
   is the **actor** attributed from the identity (not a placeholder)? (Regulated domains: auditability is a
   hard requirement.)
9. **Robustness** — malformed JSON / wrong content-type → graceful 4xx, **no 500**.
10. **Observability** — are request/access **logs actually emitted** to stdout in the running pod? metrics/health?
11. **Failure modes** — dependency down (DB/queue/downstream) behaves as designed (best-effort vs fail);
    events not silently dropped.
12. **Domain invariants** — the service-specific rules from the PRD/architecture.

## Severity + verdict (the QA report format)
- **🔴 Blocker** — must fix before prod (security, data-integrity, auditability, any 500/data-loss). Gates promotion.
- **🟠 Major** — should fix (integrity/observability gaps).
- **🟡 Minor / confirm-intent** — document or confirm the intended behaviour.
- End with an explicit **promotion verdict** (ready / not-ready + why) and the fix sequence.

## The loop (fix → redeploy → RE-VERIFY LIVE)
QA find → fix → merge → **Kargo redeploys to dev** → **re-run the QA pass against the converged live image**
→ confirm green. **Verify on the actual running/converged pod** — a rollout leaves old+new pods briefly, so
match the pod on the new image digest, not just the deploy's tag (a stale pod gives false results — this
bit us on the M2 re-check).

## How to run it
- Spawn a **QA agent** (or run the QA discipline) with an **in-cluster harness**: `kubectl exec -i <pod> --
  python -` piped a script (readOnlyRootFS blocks `kubectl cp`), or curl the dev ingress. Assert
  expected-vs-actual per case with a PASS/FAIL tally + the severity report. Keep the harness in the repo
  (`tests/qa/` or the story) so it's re-runnable each promotion.
- Reference implementation: the ktayl-underwriting QA pass (48 core checks + severity report + the M2
  root-cause chain). See [[project_ktayl_underwriting]].

## Relationship to the other gates
- **testing.md (L0–L4)** = pre-merge CI on the code. **QA gate = L5 / live acceptance** on the deployed dev
  service. Both are required; neither replaces the other.
- **bmad-compliance.md** governance gate + **gitops.md** Kargo prod-promotion: the prod PR is only opened
  after the QA gate is clean.
