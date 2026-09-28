# Org-Wide Testing Standard

## The 5 Layers

| Layer | What it checks | Speed | When it runs |
|---|---|---|---|
| **L0 — Static** | Lint, format, types, YAML schema | < 1 min | Every push, every branch |
| **L1 — Unit** | Pure logic, no external deps, mocks everything | < 5 min | Every push |
| **L2 — Integration** | Real DB, real queue, mocked HTTP | < 15 min | PR to `main` |
| **L3 — Contract** | API shape matches what consumers expect | < 5 min | PR to `main` |
| **L4 — E2E / Smoke** | Full happy path on real infra | < 10 min | PR to `main` |

## CI Gate Mapping

Two branches only (`dev` + `main`) — staging was removed with the staging environment.

```
dev push        →  L0 + L1                       (~5 min)
PR → main       →  L0 + L1 + L2 + L3 + L4        (blocking; this is the prod gate)
```

**Fail-fast rule:** L0 before L1 before L2. Never spin up a DB if linting fails.

**L5 — the QA gate (live dev acceptance), MANDATORY before prod promotion.** L0–L4 prove the code in
isolation/mocks; they do **not** catch integration/deploy/runtime/config bugs (e.g. the alembic
`fileConfig` that disabled all logging live, an unauthenticated API, an unlocked bound record). After a
service is live on **dev**, a **QA agent runs an adversarial test pass against the running service**, and
the prod-promotion PR is blocked until it's clean. Green CI is **not** sufficient to promote. See
`.claude/rules/qa-gate.md` (scope, severities, the fix→redeploy→re-verify-live loop).

## Language Matrix

| Stack | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|
| **Python (Frappe)** | ruff + mypy | pytest | bench run-tests + httpx | schemathesis | kubectl exec + httpx |
| **Python (scripts)** | ruff + mypy | pytest | pytest + testcontainers | — | manual |
| **Go** | golangci-lint | go test ./... | go test + testcontainers | openapi-validator | httpx / curl |
| **TypeScript** | eslint + tsc | vitest | vitest + MSW | — | Playwright |
| **YAML / Helm** | yamllint + kubeconform | helm lint | helm template + kube-score | — | ArgoCD diff |
| **HCL (OpenTofu)** | tofu fmt + validate | — | tofu plan (dry-run) | — | manual |
| **Ansible** | ansible-lint | molecule test | molecule converge | — | manual |

## Repo Classification

| Tier | Repos | Required layers |
|---|---|---|
| **A — Business logic** | `minicloud-erpnext`, `minicloud-plane`, `platform-demo` | L0 → L4 (full) |
| **B — Infrastructure code** | `minicloud-gitops`, `minicloud-opentofu`, `minicloud-ansible` | L0, L2 (plan/dry-run), L4 (ArgoCD diff) |
| **C — UI / docs** | `minicloud-backstage`, `ktayl-solution-web`, `minicloud-platform-docs` | L0, L1, L4 (Playwright) |
| **D — Tooling / ops** | `minicloud-ops`, `minicloud-open-webui`, `minicloud-onlyoffice` | L0, L1 |

### The tier's required layers are MANDATORY — "unit only" is the anti-pattern (2026-09-28)

**A Tier-A service is NOT Done, and MUST NOT be promoted to prod, with only L0+L1.** The by-far most common
failure observed (ktayl-underwriting was built with **L0+L1 only**, L1 heavily mocked) is skipping the
middle+top of the pyramid. Each skipped layer hides a distinct, real bug class — the QA gate then has to
catch live what a cheap pre-merge test should have:

| Layer | Catches (that unit-with-mocks CANNOT) | Real miss this session |
|---|---|---|
| **L2 Integration** (real DB/queue, testcontainers/compose) | actual schema/migrations/constraints/transactions/ORM behaviour | the alembic startup migration disabling all loggers; real Postgres semantics |
| **L3 Contract** (your API shape ↔ consumers; **your calls ↔ the collaborator's real contract**) | wire-format / schema drift at a service boundary | the **RFC3339 datetime** the app sent that policy-service rejected (`400`) — a contract test would have failed pre-merge |
| **L4 E2E / Smoke** (real happy path on real infra) | wiring/config/auth/deploy runtime bugs | unauthenticated API, live auth/JWKS/netpol, self-migration |

**Mock discipline (the core lesson).** A mock encodes an **assumption** about a collaborator. If the
assumption is wrong, the mocked unit test stays **green while prod fails** (exactly the RFC3339 and
logging bugs). Therefore: **every mocked boundary MUST be backed by an L3 contract test or an L2 real
integration that validates the assumption against the actual collaborator.** A boundary that is only ever
mocked is untested, not tested.

**Enforcement.** The tier's full layer set is part of the **Definition of Done** (a story is not Done on
unit alone — see `agile-execution.md`) and the **prod-promotion gate** (`gitops.md`): CI must actually run
L2/L3/L4 for Tier-A repos, and the live **QA gate** (`qa-gate.md`) is the backstop, not the substitute.
When building a Tier-A story, generate the **required layers**, not just unit tests. Reference backfill:
ktayl-underwriting (L2 integration + L3 contract against the policy-service OpenAPI + L4 smoke).

## Mandatory Conventions

### Directory layout (every repo)

```
tests/
  unit/         # L1 — pure logic, no external deps
  integration/  # L2 — real DB / queue
  e2e/          # L4 — smoke against real cluster
  fixtures/     # shared test data and factory functions
```

### Rules

1. **`make test`** runs L1 locally — no Docker, no network, < 5 min
2. **`make test-integration`** runs L2 with Docker Compose
3. **Coverage threshold: 70%** on business logic files (excludes hooks, `__init__.py`, scripts)
4. Every new public function or API endpoint → at least one happy-path + one failure test
5. No `# noqa` / `// nolint` without an inline comment explaining the exception
6. Test file names mirror the module: `dsn_generator.py` → `test_dsn_generator.py`
7. Fixtures live in `tests/fixtures/` — never inline large data blobs in test functions

## Rollout Plan

| Week | Repo | Tier | Deliverable |
|---|---|---|---|
| 1 | `minicloud-erpnext` | A | L0 + L1 — ruff/mypy + pytest (108 tests, 76% cov) ✅ |
| 2 | `platform-demo` | A | L0 + L1 — golangci-lint + go test |
| 3 | `minicloud-plane` | A | L0 + L1 — golangci-lint + go test |
| 4 | `minicloud-gitops` | B | L0 — yamllint + kubeconform + helm lint |
| 5+ | remaining repos | C/D | L0 + L1 in parallel |

## Reference: minicloud-erpnext (Tier A, Python/Frappe)

Pattern for all Tier A Python repos.

```
tests/
  conftest.py              # mock frappe via sys.modules (no bench needed)
  fixtures/
    employees.py           # JEAN_DUPONT, MARIE_LECLERC, MISSING_NIR, DARTAGNAN, FLOAT_AMOUNTS
    crm_responses.py       # ACCEPTE, REJETE, SOAP_FAULT, EMPTY, TRAITEMENT_SANS_ERREUR
  unit/
    test_dsn_generator.py  # 55 tests — CRLF, UTF-8, S10/S20/S90 blocks
    test_dsn_submitter.py  # 23 tests — CRM XML parsing, submit_dsn() with mocked requests.post
    test_api_helpers.py    # 15 tests — contract type codes, warnings collection
    test_facturx.py        # 15 tests — CII XML (Factur-X Minimum profile)
```

**Key pattern — mock frappe without a running bench:**
```python
# tests/conftest.py
import sys
from unittest.mock import MagicMock
_frappe = MagicMock(name="frappe")
for _mod in ("frappe", "frappe.utils", "frappe.utils.file_manager", "frappe.utils.pdf"):
    sys.modules.setdefault(_mod, _frappe)
```

**Local commands:**
```bash
pip install -r requirements-test.txt
make lint       # L0: ruff + mypy
make test-cov   # L1: pytest --cov --cov-fail-under=70
make fmt        # auto-fix formatting
```

**CI jobs (`.github/workflows/test.yml`):**
```yaml
jobs:
  lint:       # ruff check + ruff format --check + mypy  (every push)
  test-unit:  # pytest tests/unit/ --cov --cov-fail-under=70  (needs: lint)
```
