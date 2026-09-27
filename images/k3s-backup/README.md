# k3s-backup image

Self-contained backup tool image (alpine + sqlite + rclone + age) for the k3s control-plane
backup CronJob. Built + pushed manually (no CI):

```bash
docker build --platform linux/amd64 -t harbor.10.0.0.200.nip.io/library/k3s-backup:2.0 images/k3s-backup
docker save harbor.10.0.0.200.nip.io/library/k3s-backup:2.0 -o /tmp/k3s-backup.tar
crane push /tmp/k3s-backup.tar harbor.10.0.0.200.nip.io/library/k3s-backup:2.0 && rm /tmp/k3s-backup.tar
```

`:2.0` adds `age`; `:1.0` was sqlite+rclone only.
