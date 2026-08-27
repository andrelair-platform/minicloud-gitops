# Optional staging overlay

**The platform default is 2 environments: `dev` + `prod`.** Staging is opt-in.

This overlay is kept as a ready-made template but is intentionally **not** an
active environment (leading `_` marks it opt-in, and no ArgoCD Application
points at it). Only add staging for services that genuinely need a third gate —
e.g. certification work (`ktayl-policy-service` / CERT-1) or demo services that
exercise a staging promotion (`platform-demo`).

## To activate staging for a service

1. Rename the copied dir: `_staging-optional/` → `staging/`.
2. Replace `SERVICE_NAME` throughout (kustomization, ingress, quota, rolebinding).
3. Add the `SERVICE_NAME-staging` namespace to the AppProject
   (`manifests/argocd-project/00-project.yaml`).
4. Add an ArgoCD Application `apps/workloads/SERVICE_NAME-staging.yaml`
   (manual sync — promote to staging via PR after dev is validated).
5. Add a NetworkPolicy set in `manifests/network-policies/SERVICE_NAME-staging.yaml`.

Promotion flow with staging: `dev (auto) → staging (PR) → prod (PR)`.
Without staging (default): `dev (auto) → prod (PR)`.
