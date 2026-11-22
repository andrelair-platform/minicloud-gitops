#!/usr/bin/env bash
# Re-sync the andrelair-platform org Actions secrets from their sources of truth.
#
# WHY: the #9 incident (2026-11-22) was *drift* — the GitHub org GITOPS_TOKEN had an old, under-scoped
# token while Vault held the correct one. This script makes the Vault→GitHub sync a repeatable one-liner
# so the two can't silently diverge. (The scheduled .github/workflows/token-health-check.yml is the
# early-warning that tells you to run this.)
#
# SOURCES OF TRUTH:
#   GITOPS_TOKEN      ← Vault  secret/platform/ci-secrets : gitops-token   (classic PAT: repo + write:packages + project + workflow)
#   MINICLOUD_CA_CERT ← local  ~/minicloud-ca.crt                          (raw PEM — never base64)
#   GPG_PRIVATE_KEY   ← local  GPG keyring, key FD6D39D681DEFA34
#
# REQUIREMENTS (run from the Mac):
#   - gh authed with admin:org   (controller gh does NOT have this → must run here, not on the controller)
#   - ssh access to `controller` (its ~/.vault-ops-token reads secret/platform)
#   - the local GPG private key + ~/minicloud-ca.crt
#
# Secrets are streamed via stdin pipes — never written to a file, a variable, or shell history.
#
#   bash scripts/set-org-secrets.sh
set -euo pipefail

ORG="andrelair-platform"
VAULT_ENV='export VAULT_ADDR=https://vault.10.0.0.200.nip.io VAULT_SKIP_VERIFY=true VAULT_TOKEN=$(cat ~/.vault-ops-token)'

command -v gh  >/dev/null || { echo "gh not found"; exit 1; }
gh auth status 2>&1 | grep -q 'admin:org' || { echo "gh token lacks admin:org — can't set org secrets"; exit 1; }

echo "→ GITOPS_TOKEN  (Vault secret/platform/ci-secrets:gitops-token, via controller)"
ssh controller "${VAULT_ENV}; vault kv get -field=gitops-token secret/platform/ci-secrets" \
  | gh secret set GITOPS_TOKEN --org "$ORG" --visibility all

echo "→ MINICLOUD_CA_CERT  (~/minicloud-ca.crt, raw PEM)"
gh secret set MINICLOUD_CA_CERT --org "$ORG" --visibility all < "$HOME/minicloud-ca.crt"

echo "→ GPG_PRIVATE_KEY  (local GPG keyring FD6D39D681DEFA34)"
gpg --armor --export-secret-keys FD6D39D681DEFA34 \
  | gh secret set GPG_PRIVATE_KEY --org "$ORG" --visibility all

echo "✓ org secrets re-synced. Verify:  gh secret list --org $ORG"
