# CI / Container Registry Rules

**All repos push to `harbor.10.0.0.200.nip.io` via Tailscale.**
Registry path: `harbor.10.0.0.200.nip.io/library/<name>`

**Required secrets (all repos):** `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`, `MINICLOUD_CA_CERT`, `HARBOR_USER`, `HARBOR_PASSWORD`, `GITOPS_TOKEN`, `GPG_PRIVATE_KEY`

All 7 are **org-level secrets** on `andrelair-platform` (set 2026-07-15, visibility: all). New repos inherit automatically.

To refresh/rotate org secrets (requires `admin:org` scope):
```bash
! gh auth refresh -h github.com --scopes admin:org
! bash /tmp/set-org-secrets.sh   # pulls live from Vault + local GPG keyring
```

## Standard CI step sequence

```yaml
- uses: tailscale/github-action@v4.1.3
  with:
    oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
    oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
    tags: tag:ci

- name: Trust minicloud CA
  run: |
    sudo mkdir -p /etc/docker/certs.d/harbor.10.0.0.200.nip.io
    echo "${{ secrets.MINICLOUD_CA_CERT }}" \
      | sudo tee /etc/docker/certs.d/harbor.10.0.0.200.nip.io/ca.crt
    echo "${{ secrets.MINICLOUD_CA_CERT }}" \
      | sudo tee /usr/local/share/ca-certificates/minicloud-ca.crt
    sudo update-ca-certificates
```

## Key CI Gotchas

**CA cert in custom images:** Never commit `certs/minicloud-ca.crt` to a public repo. Inject at build time: `ARG CA_CERT` in Dockerfile + `build-args: CA_CERT=${{ secrets.MINICLOUD_CA_CERT }}` in CI. Local: `docker build --build-arg CA_CERT="$(cat ~/minicloud-ca.crt)" .`

**MINICLOUD_CA_CERT is raw PEM — NEVER `base64 -d` it.**

**Tailscale OAuth gotcha:** The `tag:ci` tag must exist in the Tailscale ACL policy BEFORE the first CI run.

**Cloudflare WAF blocks `User-Agent: AsyncOpenAI/Python*`:** Returns HTTP 403. Fix: `default_headers={"User-Agent": "minicloud-eval/1.0"}` in `OpenAI()` constructor.

## Branch strategy (all repos)

- `dev` — direct push, no signing, CI builds `dev-<sha>` image
- `staging` — PR required, cosign-signed image
- `main` — PR + GPG required, cosign + SBOM, bumps gitops manifest
