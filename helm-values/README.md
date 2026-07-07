# helm-values/

All Helm values for platform tools live here. This is the single source of truth for
third-party chart configuration. minicloud-ansible no longer holds deployment config.

## All tools are ArgoCD-managed (Combo 2)

ArgoCD fetches each upstream chart + these values and manages the full lifecycle.
Edit a values file → commit → ArgoCD syncs automatically within 3 minutes.

| File | Chart | ArgoCD App | Namespace |
|---|---|---|---|
| `argocd-values.yaml` | argo/argo-cd 9.5.13 | `argo-cd` | argocd |
| `authentik-values.yaml` | authentik/authentik 2026.5.3 | `authentik` | authentik |
| `backstage-values.yaml` | backstage/backstage 2.7.0 | `backstage` | backstage |
| `cert-manager-values.yaml` | jetstack/cert-manager v1.20.2 | `cert-manager` | cert-manager |
| `chaos-mesh-values.yaml` | chaos-mesh/chaos-mesh 2.8.2 | `chaos-mesh` | chaos-mesh |
| `falco-values.yaml` | falcosecurity/falco 9.1.0 | `falco` | falco |
| `gatekeeper-values.yaml` | gatekeeper/gatekeeper 3.22.2 | `gatekeeper` | gatekeeper-system |
| `harbor-values.yaml` | harbor/harbor 1.18.3 | `harbor` | harbor |
| `keda-values.yaml` | kedacore/keda 2.19.0 | `keda` | keda |
| `kube-prometheus-stack-values.yaml` | prometheus-community/kube-prometheus-stack 84.5.0 | `kube-prometheus-stack` | monitoring |
| `langfuse-values.yaml` | langfuse/langfuse 1.5.37 | `langfuse` | langfuse |
| `loki-values.yaml` | grafana/loki 7.0.0 | `loki` | observability |
| `nats-values.yaml` | nats/nats 2.12.6 | `nats` | messaging |
| `nextcloud-values.yaml` | nextcloud/nextcloud 9.1.3 | `nextcloud` | nextcloud |
| `nfs-provisioner-values.yaml` | nfs-subdir-external-provisioner 4.0.18 | `nfs-provisioner` | nfs-provisioner |
| `nginx-ingress-values.yaml` | nginx-stable/nginx-ingress 2.5.1 | `nginx-ingress` | ingress-nginx |
| `ollama-values.yaml` | otwld/ollama 1.61.0 | `ollama` | ai |
| `ollama-secondary-values.yaml` | otwld/ollama 1.61.0 | `ollama-secondary` | ai |
| `ollama-tertiary-values.yaml` | otwld/ollama 1.61.0 | `ollama-tertiary` | ai |
| `open-webui-values.yaml` | open-webui/open-webui 14.4.0 | `open-webui` | ai |
| `podinfo-values.yaml` | podinfo/podinfo 6.11.2 | `podinfo` | podinfo |
| `polaris-values.yaml` | fairwinds/polaris 6.x | `polaris` | polaris |
| `postgresql-ai-values.yaml` | bitnami/postgresql 18.6.4 | `postgresql-ai` | ai |
| `promtail-values.yaml` | grafana/promtail 6.17.1 | `promtail` | observability |
| `vault-values.yaml` | hashicorp/vault 0.33.0 | `vault` | vault |
| `velero-values.yaml` | vmware-tanzu/velero 12.0.1 | `velero` | velero |

## Notes

- `harbor-values.yaml` intentionally omits `harborAdminPassword` (stored at `~/.harbor-admin` on controller).
  ArgoCD `ignoreDifferences` in `apps/harbor.yaml` prevents password-field sync attempts.
- `argo-cd` (ArgoCD self-management) has no `automated:` sync policy — manual sync only, to avoid accidental self-disruption.
- `cert-manager`, `gatekeeper`, `keda`, `nfs-provisioner` use `sync-wave` annotations so infrastructure
  dependencies come up before the apps that need them (on fresh cluster rebuild).
