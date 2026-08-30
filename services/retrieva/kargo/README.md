# retrieva — PARKED for Kargo promotion

Kargo promotes **one immutable artifact** from dev to prod. Retrieva breaks that
assumption: the **frontend bakes `NEXT_PUBLIC_API_URL` at build time**, so the dev
image and the prod image are *different builds* (dev → Harbor with a `dev-*` tag,
prod → ghcr with a SHA tag). There is no single artifact to move dev → prod, so a
Kargo Warehouse/Stage pipeline would be lying about what it promotes.

This dir is intentionally a README only (excluded in `apps/platform/kargo-projects.yaml`).

## What would make retrieva Kargo-promotable

- Stop baking the API URL into the frontend image — inject it at **runtime**
  (env var read by the browser via a `/config.js` or a Next.js runtime config),
  so the *same* image runs in dev and prod. Then a single ghcr SHA artifact can be
  promoted across stages like the other services.
- Alternatively, promote **only the backend** (not env-baked) with a Warehouse on
  `ghcr.io/andrelair-platform/retrieva-backend`, and keep the frontend on its
  per-env build. This is a partial pipeline — deferred until the runtime-config
  change above is decided.

Until then, retrieva keeps its current flow: CI builds per-env images, dev auto-syncs,
prod moves via a CODEOWNERS-gated PR (manual `kustomize edit set image`).
