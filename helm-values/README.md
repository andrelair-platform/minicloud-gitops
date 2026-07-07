# helm-values/

All Helm values for platform tools live here. This is the single source of truth for
third-party chart configuration. minicloud-ansible no longer holds deployment config.

## Two deployment modes

### ArgoCD-managed (Combo 2)
ArgoCD fetches the upstream chart + these values and manages the full lifecycle.
Edit a values file → commit → ArgoCD syncs automatically.

| File | Chart | ArgoCD App |
|---|---|---|
| `vault-values.yaml` | hashicorp/vault 0.33.0 | `vault` |
| `nextcloud-values.yaml` | nextcloud/nextcloud 9.1.3 | `nextcloud` |
| `langfuse-values.yaml` | langfuse/langfuse 1.5.37 | `langfuse` |
| `polaris-values.yaml` | fairwinds/polaris 6.x | `polaris` |

### Direct helm upgrade (pending ArgoCD migration)
These are still deployed via `helm upgrade` on the controller.
Values are tracked here for version control; deploy with:

```bash
# scp to controller then helm upgrade — see CLAUDE.md for full commands
scp helm-values/<name>-values.yaml controller:/tmp/
ssh controller "helm upgrade <name> <repo>/<chart> -n <ns> -f /tmp/<name>-values.yaml"
```

| File | Tool | Namespace |
|---|---|---|
| `kube-prometheus-stack-values.yaml` | kube-prometheus-stack | monitoring |
| `nginx-ingress-values.yaml` | nginx-stable/nginx-ingress | ingress-nginx |
| `authentik-values.yaml` | authentik | authentik |
| `ollama-values.yaml` | custom | ai |
| `ollama-secondary-values.yaml` | custom | ai |
| `open-webui-values.yaml` | open-webui | ai |
| `postgresql-ai-values.yaml` | bitnami/postgresql | ai |
| `falco-values.yaml` | falcosecurity/falco | falco |
| `nats-values.yaml` | nats | messaging |
| `velero-values.yaml` | vmware-tanzu/velero | velero |
| `argocd-values.yaml` | argo/argo-cd | argocd |
| `backstage-values.yaml` | backstage/backstage | backstage |
