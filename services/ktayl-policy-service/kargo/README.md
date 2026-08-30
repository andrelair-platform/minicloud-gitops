# ktayl-policy-service — PARKED for Kargo promotion

Kargo tracks and promotes an **immutable** artifact. ktayl-policy-service prod is
still on the *pre-hybrid-registry* pattern: its prod overlay pulls
`harbor.10.0.0.200.nip.io/library/ktayl-policy-service:**latest**` — a **mutable**
tag on the in-cluster Harbor. There is no immutable SHA for a Warehouse to observe,
and "promote `:latest`" is meaningless (the tag never changes).

This dir is intentionally a README only (excluded in `apps/platform/kargo-projects.yaml`).

## What would make it Kargo-promotable

1. Put it on the **hybrid registry** like the other services: CI dual-pushes prod
   images to `ghcr.io/andrelair-platform/ktayl-policy-service:<sha>` (immutable),
   and the prod overlay uses `newName: ghcr.io/...` + a SHA `newTag` (see
   `services/platform-demo/minicloud-1/prod/kustomization.yaml`).
2. Then copy a wired pipeline (e.g. `services/platform-demo/kargo/`), point the
   Warehouse at `ghcr.io/andrelair-platform/ktayl-policy-service`, set the
   kustomize image key to the Harbor base name, and remove this dir from the
   exclude list in `apps/platform/kargo-projects.yaml`.

If you'd rather keep watching Harbor directly, the Kargo controller also needs the
minicloud CA mounted (to verify Harbor TLS) and a Harbor robot `image` credential —
extra moving parts the ghcr/SHA route avoids.
