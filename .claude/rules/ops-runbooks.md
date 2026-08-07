# Ops Runbooks (Mac-side)

## Platform Recovery Check (minicloud-ops)

Installed on controller only. Entry point: `/usr/local/bin/minicloud-recovery-check`

```bash
ssh controller "minicloud-recovery-check"
ssh controller "cat /var/log/minicloud-recovery.log"   # last run report
ssh controller "cd ~/minicloud-ops && git pull origin main"   # update
```

NAT persistence is **automated** (`restore-cluster-nat.service`). After power failure, only MinIO needs a manual restart (caches disk-full state in memory):
```bash
ssh controller "docker restart minio"
```

**ArgoCD SSA + argocd-cm gotcha:** New `configs.cm:` keys in `argocd-values.yaml` silently fail to appear after sync (helm CSA manager owns `.`). Apply directly via kubectl patch:
```bash
ssh controller "kubectl patch configmap argocd-cm -n argocd --type merge -p '{\"data\":{\"<key>\":\"<value>\"}}'"
```

## ktayl-solution-web — Emergency Manual Push (if CI is down)

```bash
cd ~/Developer/cloudplateform/ktayl-solution-web
SHORT_SHA=$(git rev-parse --short HEAD)
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build --platform linux/amd64 \
  -t "ktayl-solution-web:${SHORT_SHA}" .
docker save "ktayl-solution-web:${SHORT_SHA}" -o /tmp/ktayl-web.tar
crane push /tmp/ktayl-web.tar "harbor.10.0.0.200.nip.io/library/ktayl-solution-web:${SHORT_SHA}"
rm /tmp/ktayl-web.tar
```

## RAG Pipeline

Two services in the `ai` namespace:

| Service | Port | Purpose |
|---|---|---|
| markitdown-proxy | 8000 | PDF/images→Docling, Office→MarkItDown |
| rag-ingest | 8001 | Full pipeline: convert→chunk→embed→ragdb |

```bash
kubectl --context minicloud port-forward -n ai svc/rag-ingest 8001:8001 &
curl -s -X POST http://localhost:8001/ingest \
  -F "file=@/path/to/document.pdf" \
  -F "collection=<COLLECTION_UUID>" \
  -F "source=My Document Title" \
  -F "doc_type=policy" | python3 -m json.tool
kill %1
```

`doc_type` values: `policy`, `endorsement`, `annexe`, `regulatory`, `tariff`, `internal`

## Vaultwarden

**URL:** `https://vault-pw.devandre.sbs` — login via Authentik SSO
**Image:** `ghcr.io/timshel/vaultwarden:1.34.1-6` (Timshel fork required for SSO button)
**bw CLI on controller:** `~/.local/share/bw-compat/bw` (v2024.6.0 — v2026+ incompatible)

```bash
BW=~/.local/share/bw-compat/bw
$BW config server https://vault-pw.devandre.sbs
BW_SESSION=$($BW unlock --passwordenv BW_PASSWORD --raw)
$BW --session $BW_SESSION list items --folderid <folder-id>
$BW lock
```

## Cloudflare

Credentials in Vault `secret/platform/cloudflare`: `api-token`, `account-id`, `r2-access-key-id`, `r2-secret-access-key`, `r2-s3-endpoint`.

```bash
# Read token from Vault:
VAULT_ROOT=$(ssh controller "cat ~/.vault-root-token")
/usr/bin/curl -sk --cacert ~/minicloud-ca.crt \
  -H "X-Vault-Token: $VAULT_ROOT" \
  "https://vault.devandre.sbs/v1/secret/data/platform/cloudflare" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']['data']; print(d['api-token'])"
```

Cloudflare Tunnel runs as systemd on controller. Config: `~/.cloudflared/config.yml`. Use `Restart=always` + `StartLimitIntervalSec=0` in unit file.

```bash
# Add new DNS route:
ssh controller "~/.local/bin/cloudflared tunnel route dns minicloud newapp.devandre.sbs"
```

**Key gotcha:** Every Ingress with a `devandre.sbs` host rule needs a matching `tls:` entry.

## Controller Disk Management

Controller `/dev/nvme0n1p5` is 98G. Budget: MinIO~33GB, k3s snapshots~6.5GB, OS~15GB → ~38GB headroom.

```bash
ssh controller "df -h / && du -sh /srv/backups/k3s/ /srv/backups/minio/ 2>/dev/null | sort -rh"
```

**Non-sudo cleanup:**
```bash
ssh controller "ls /home/ktayl/.local/share/claude/versions/ | sort -V | head -n -1 | xargs -I{} rm -rf /home/ktayl/.local/share/claude/versions/{}"
ssh controller "rm -rf /home/ktayl/.local/share/Trash/files/* /home/ktayl/snap/firefox/common/.cache"
```

**After freeing disk — restart MinIO** (caches the disk-full state in memory):
```bash
ssh controller "docker restart minio && sleep 5 && docker ps --filter name=minio --format '{{.Status}}'"
```

**Journal vacuum (interactive sudo required):**
```bash
! ssh -t controller "sudo journalctl --vacuum-size=200M"
```

## Kine/SQLite Control Plane Backup

| | k8s CronJob | Controller systemd timer |
|---|---|---|
| Schedule | 03:30 UTC | 02:30 UTC (before Velero) |
| Method | `sqlite3 .backup` (WAL-safe) | `sqlite3 .dump` piped via SSH |
| MinIO bucket | `k3s-backup/` | `db-backups/kine/` |
| Retention | 7 files | 30 days |
| k8s dependency | Yes | **No** — runs on controller |

GitOps: `manifests/backup-dr/01-k3s-sqlite-backup.yaml`. Script on controller: `/home/ktayl/bin/kine-backup.sh`.

**Health check:**
```bash
ssh controller "systemctl status kine-backup.timer --no-pager && \
  ~/.local/bin/mc ls minilocal/db-backups/kine/ | tail -3 && \
  ~/.local/bin/mc ls minilocal/k3s-backup/ | tail -3"
```

**Restore (set-hog disk replaced):** fresh k3s install → stop k3s → restore from either bucket → start k3s.
