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
