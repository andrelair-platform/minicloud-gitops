# _template-helm — GAP wrapper-chart scaffold for a custom app

Copy this for a NEW custom service. A service = **its own thin Helm chart** (`Chart.yaml` depends on
the `minicloud-app-deployment` library chart) + `values{,-dev,-prod}.yaml` + a `templates/` for
service-specific extras + **2 ArgoCD Applications, one Helm source each**. No kustomize, no
multi-source `$values`, no separate satellites source. See `docs/helm-golden-path.md` (ADR).

## Onboard checklist
1. Copy `helm/` → `services/<svc>/helm/`; replace `SERVICE_NAME` everywhere; set the library
   `dependencies.version` in `Chart.yaml` to the current chart version.
2. `cd services/<svc>/helm && helm dependency update .` → **commit `Chart.lock`** (ArgoCD runs
   `helm dependency build` to fetch the dep; `charts/` is gitignored via `services/*/helm/charts/`).
3. Fill `values.yaml` (subchart config under `minicloud-app-deployment:` + wrapper-local keys) and
   the per-env `values-{dev,prod}.yaml`.
4. Put service-specific extras in `templates/` (DB, AnalysisTemplate, SSO Ingress, ExternalSecret…).
   A simple single-host service can instead use the **library** Ingress + Certificate (see values).
5. Copy `apps/*` → `apps/workloads/<svc>-{dev,prod}.yaml`; keep `helm.releaseName: <svc>`.
6. Add the namespaces to the AppProject. Kargo promotion edits `minicloud-app-deployment.image.tag`.

## DNS — internal (default) vs public org app
Follow the one convention in `docs/dns-naming-and-externaldns.md`. **Env is a subdomain PREFIX, prod is
the clean name** (dev = `<svc>.dev.<zone>`, prod = `<svc>.<zone>`).
- **Internal (default in the values):** Tailscale-only `<svc>.dev.10.0.0.200.nip.io` / `<svc>.10.0.0.200.nip.io`.
  Nothing else to do — nip.io self-resolves.
- **Public org app:** move onto the org namespace **`<svc>.ktayl.devandre.sbs`** and add the ExternalDNS
  opt-in (see the *PUBLIC ORG APP* block in `values-prod.yaml`). The `ktayl.devandre.sbs` host **is** the
  opt-in (ExternalDNS `domainFilters`); the `external-dns.alpha.kubernetes.io/target` annotation makes it
  a CNAME to the Cloudflare Tunnel → the DNS record is created automatically (no manual
  `cloudflared tunnel route dns`). **Never** use `www`/apex `devandre.sbs` (that's the personal
  portfolio) or `retrieva.online` (separate product). Companion one-time step for zero-touch public
  onboarding: a wildcard `*.ktayl.devandre.sbs` cloudflared rule + cert (controller-side).

## Gotchas (proven converting 5 services — see gitops.md for the full list)
- **`helm.releaseName` is mandatory** — the library uses it for `fullname`; without it the workload
  takes the ArgoCD app name.
- **`.helmignore` must NOT list `charts/`** (breaks local render) — gitignore it instead; commit `Chart.lock`.
- **Escape non-Helm `{{ }}`** in `templates/` — ESO output-templates and Argo-Rollouts args must be
  backtick-wrapped `{{ ` + `<expr>` + ` }}`; and **no `{{ }}` in YAML comments** (Helm parses them).
- **Zero-downtime migration** off an existing manifest — set subchart `selectorLabels: {app: <name>}`
  to match the live selector → in-place rolling update, no delete/downtime. Keep stateful extras
  (a DB StatefulSet) verbatim so their immutable spec is identical → data preserved.

## Validate locally
```bash
cd services/<svc>/helm && helm dependency update . && helm template <svc> . -f values-dev.yaml
```

## Library chart publish (maintainers)
`helm package charts/minicloud-app-deployment` → `helm push` to `oci://ghcr.io/andrelair-platform`
(+ `oci://harbor.../library`). Bump `Chart.yaml` version; bump `dependencies.version` in each wrapper
`Chart.yaml` + re-run `helm dependency update` to refresh `Chart.lock`.
