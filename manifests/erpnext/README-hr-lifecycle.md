# HR-12 — J/M/L lifecycle event seam (ERPNext producer side)

ERPNext (`erpnext_hr_lifecycle` custom app, repo `minicloud-erpnext`) emits **signed** Joiner/Mover/
Leaver events on the relevant HR doc events, in a background job (never blocks the HR transaction):

```
Employee after_insert / Promotion·Transfer submit / Separation submit
   → HMAC-SHA256 sign (HR_LIFECYCLE_SIGNING_KEY)
   → NATS JetStream HR_LIFECYCLE  subject hr.lifecycle.<joiner|mover|leaver>   (durable backbone)
   → POST HR_N8N_WEBHOOK_URL                                                    (non-access fan-out)
```

ktayl-iam v3 adds its own durable consumer on `HR_LIFECYCLE` later to react for **access** (Joiner →
workspace birthright, Leaver → revoke, Mover → recompute). **ERPNext never writes Authentik.**

## Pieces here
- **`60-hr-lifecycle-stream-init.yaml`** — idempotent Job that creates the `HR_LIFECYCLE` stream
  (subjects `hr.lifecycle.>`). Runs in `erp`; `allow-cluster-clients` in `messaging` permits erp→nats:4222.
- **`erpnext-values.yaml`** — injects `HR_LIFECYCLE_SIGNING_KEY` + `HR_N8N_WEBHOOK_URL` into the
  gunicorn and worker pods from the secret `erpnext-hr-lifecycle`.

## Secret `erpnext-hr-lifecycle` — bootstrap (NOT yet Vault/ESO)

The HMAC signing key is a **bootstrapped in-cluster secret**, not yet Vault-managed. Writing to Vault
needs the root token (age-encrypted on the controller; the age identity lives only in Vaultwarden
break-glass) — the same **write-token-blocked** deferral already accepted for ghcr/cloudflare. ArgoCD
does not prune it (no tracking-id). Re-create after a cluster rebuild:

```bash
# on the controller
KEY=$(openssl rand -hex 32)
kubectl create secret generic erpnext-hr-lifecycle -n erp \
  --from-literal=HR_LIFECYCLE_SIGNING_KEY="$KEY" \
  --from-literal=HR_N8N_WEBHOOK_URL="<n8n production webhook URL, or empty>" \
  --dry-run=client -o yaml | kubectl apply -f -
```

**TODO (follow-up):** migrate to Vault `secret/platform/hr-lifecycle` + an ESO ExternalSecret (mirror
`01-externalsecrets.yaml`) once a Vault write token is available. The signing key must match the value
the consumers (n8n fan-out, ktayl-iam v3) verify against.

## Activate the custom app on the live pod (one-time, after the image carrying it is deployed)
```bash
POD=$(kubectl get pod -n erp -l app.kubernetes.io/component=gunicorn -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n erp "$POD" -- bench --site erp.devandre.sbs install-app erpnext_hr_lifecycle
kubectl rollout restart deployment -n erp -l app.kubernetes.io/component=gunicorn
# hooks load from sites/apps.txt (on the sites PVC) — install-app adds it there.
```

## Verify the seam live
```bash
# reusable proof: publishes a SIGNED event to HR_LIFECYCLE and re-verifies the signature on read
minicloud-ops/scripts/hr-lifecycle/verify-stream.sh
# or from ERPNext itself once the app is live (admin):
#   POST /api/method/erpnext_hr_lifecycle.events.emit_test_event?event_type=joiner
```
