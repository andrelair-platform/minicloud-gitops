# Connectivity — SSH, kubectl, curl, PKI

## SSH Aliases (`~/.ssh/config`)

```bash
ssh controller       # ktayl@100.88.123.8 (Tailscale)
ssh set-hog          # ubuntu@10.0.0.2 via ProxyJump controller
ssh fast-skunk       # ubuntu@10.0.0.4 via ProxyJump
ssh fast-heron       # ubuntu@10.0.0.7 via ProxyJump
ssh star-kitten      # ubuntu@10.0.0.8 via ProxyJump
ssh swift-mac        # andre@10.0.0.10 via ProxyJump (MacBook Pro 2012)
```

Run infrastructure commands remotely:
```bash
ssh controller "kubectl get nodes"
ssh controller "kubectl get pods -A | grep -v Running | grep -v Completed"
```

Multi-line remote commands — use a separate file or Python script piped via scp, NOT heredocs with backticks. Local zsh expands backticks inside double-quoted SSH arguments before sending.

## kubectl from the Mac

```bash
kubectl --context minicloud get nodes        # always pass --context minicloud
kubectl --context minicloud get pods -A
```

Default context is `myAKSCluster` — always pass `--context minicloud` or set it explicitly.

OIDC contexts: `minicloud-oidc` (daily use) · `minicloud-break-glass` (static cert, emergency only)

## curl from the Mac

`/opt/anaconda3/bin/curl` is first in PATH and uses OpenSSL — it **ignores** the macOS System Keychain. Always use `/usr/bin/curl` or pass `--cacert ~/minicloud-ca.crt` for minicloud HTTPS endpoints:

```bash
/usr/bin/curl --cacert ~/minicloud-ca.crt -sI https://backstage.10.0.0.200.nip.io
```

## PKI / TLS

Root CA cert: `~/Developer/cloudplateform/minicloud-ca.crt`. Symlinked to `~/minicloud-ca.crt`. Trusted in macOS System Keychain.

- `crane` → Go TLS → respects macOS System Keychain → can push to Harbor
- `/usr/bin/curl` → macOS SecureTransport → respects System Keychain
- `/opt/anaconda3/bin/curl` → OpenSSL → **ignores** System Keychain → must pass `--cacert`

**MINICLOUD_CA_CERT is raw PEM — NEVER `base64 -d` it.**
