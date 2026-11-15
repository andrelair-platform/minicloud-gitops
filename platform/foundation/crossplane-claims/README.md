# Self-service infrastructure claims

This directory is the **home for Crossplane claims** authored via the Backstage
**"Provision a Database"** golden path (self-service surface over IDP #2, Infrastructure Orchestration).

## How it works

```
Backstage "Provision a Database"  →  opens a PR adding  <namespace>-<name>.yaml here
        │                                (a PostgresInstance claim, this XRD:
        │                                 platform/foundation/crossplane-config/05-xrd.yaml)
        ▼  CODEOWNERS-gated review (a DB holds persistent data) → merge
   ArgoCD app `crossplane-claims`  →  syncs the claim into its metadata.namespace
        ▼
   Crossplane composes  →  CNPG Cluster (2-inst) + NetworkPolicy + secret <name>-cnpg-app
```

## A claim looks like

```yaml
apiVersion: platform.minicloud/v1alpha1
kind: PostgresInstance
metadata:
  name: orders            # → CNPG cluster <name>-cnpg, secret <name>-cnpg-app
  namespace: my-app       # the consuming app's (existing) namespace
spec:
  size: small             # small=1 instance · medium=2
  storageSize: 1Gi
```

The connection secret `<name>-cnpg-app` (host/dbname/user/password) is CNPG-native and lands in the
same namespace — mount it into the app.

- **The target namespace must already exist** (claims don't create it — deploy the app first).
- **Gated, not auto-merged:** databases are more consequential than ephemeral previews, so a claim PR is
  reviewed before merge (CODEOWNERS). The *request* is self-service; the *provision* is governed.
- Docs: `developer-platform/crossplane` (the XRD/Composition) · `developer-platform/ephemeral-preview-environments`.
