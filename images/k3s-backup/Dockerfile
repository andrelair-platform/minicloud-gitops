# k3s-backup — self-contained image for the control-plane backup CronJob
# (manifests/backup-dr/01-k3s-sqlite-backup.yaml). Baked-in tools (NO runtime apk) so a
# DR backup never depends on the internet mid-incident (the 2026-08-19 bind9-flap lesson):
#   sqlite  — VACUUM INTO consistent kine snapshots
#   rclone  — push to MinIO (mirrored to R2 offsite)
#   age     — asymmetric client-side encryption (encrypt-only with the public recipient;
#             the private identity lives in Vault secret/platform/k3s-backup-age, used only
#             at restore — so a compromised set-hog cannot decrypt its own offsite backups)
FROM alpine:3.20
RUN apk add --no-cache sqlite rclone age
