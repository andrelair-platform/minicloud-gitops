# ADR: ArgoCD instant sync — GitHub webhook + reconciliation backoff

**Status:** Accepted (2026-10-18) · **Owner:** SA/TL · **Scope:** IS Foundations (Platform — GitOps delivery)
· **Layer:** Platform capability (NOT Retrieva/IS — see the two-layer model in `.claude/rules/github-projects.md`)

## Context

ArgoCD reconciles desired state (Git) ↔ live state on a **timer** (`timeout.reconciliation`, default
**180s**). With no push notification, a merge to `main` took **up to ~3 minutes** to start syncing — the
latency the owner flagged (*"auto-sync is ~3 min behind"*). GitHub can notify ArgoCD the instant a push
lands via ArgoCD's `/api/webhook` endpoint, collapsing that to seconds.

Two things had to be true for the webhook to work, and a third decision followed once it did:

1. **A public ingress for the endpoint.** ArgoCD is deliberately **Tailscale-only** (tier ① in the DNS
   ADR) — `argocd.devandre.sbs` had **no** Cloudflare-tunnel route, so every GitHub delivery fell through
   to the tunnel's catch-all **404**.
2. **Correct HTTP Host routing.** Even once routed, ingress-nginx routes on the **Host header**, and the
   ArgoCD Ingress declares **only** `argocd.10.0.0.200.nip.io` (unlike public apps, which declare both the
   nip.io and the `devandre.sbs` host). cloudflared preserved the public Host → no Ingress match → nginx
   **default-backend 404**.
3. **Once the webhook delivers instant syncs, the 180s poll is redundant for latency** — keeping it that
   aggressive just wastes git-provider + application-controller load.

## Decision

**Expose only the webhook path, rewrite the Host to the internal name, and back the reconciliation poll
off to 1h.**

1. **Path-scoped tunnel route** (`platform/networking/cloudflare-tunnel/02-configmap.yaml`) exposing
   **only** `argocd.devandre.sbs/api/webhook` → `https://10.0.0.200`. The UI/API stay off the tunnel
   (any other path → the 404 catch-all). The endpoint is **unauthenticated-by-design but HMAC-validated**
   against `argocd-secret` `webhook.github.secret`, so exposing just this path is safe.
2. **`httpHostHeader: argocd.10.0.0.200.nip.io`** on that rule so cloudflared rewrites the Host → nginx
   matches the ArgoCD Ingress and the request reaches `argocd-server`. (`originServerName` only sets the
   TLS **SNI**, not the Host — that was the second 404.)
3. **`timeout.reconciliation: 180s → 1h`** (`helm-values/minicloud-1/argocd-values.yaml`). The webhook is
   the low-latency path; the poll becomes a **correctness backstop**.

### Why keep the poll at all (not `0`) — webhook ≠ superset of the poll
The webhook and the reconcile loop do **different jobs**; the poll covers three gaps the webhook cannot:

| Gap | Why the webhook misses it |
|---|---|
| **Missed/failed deliveries** | one best-effort HTTP POST — no durable queue/retry. cloudflared restarting, a GitHub blip, or ArgoCD mid-rollout = that event is lost until the next poll. |
| **Live cluster drift (selfHeal)** | the webhook fires only on a **git push**. Out-of-band mutation (a `kubectl edit`, another controller, a node event) is **not** a push → only the periodic reconcile detects + heals it. |
| **Non-matching sources** | the webhook refreshes only apps whose **source repo** matches the push; Helm/OCI-chart or other-repo sources are picked up by the poll. |

`0` (disable) would remove the backstop entirely → a single missed delivery or any drift could persist
indefinitely. **1h** keeps worst-case convergence ≤ 1 hour while cutting routine polling ~20×. Standard
*"event for speed, poll for guarantee"*.

## Alternatives considered
- **Add `argocd.devandre.sbs` as a host on the ArgoCD Ingress** (instead of the Host rewrite) — rejected:
  widens the public surface + needs a TLS entry; the `httpHostHeader` rewrite is surgical (one path).
- **Shorten the poll** (the literal reading of "reduce the timeout") — rejected: *increases* load for zero
  latency benefit once the webhook exists. The webhook, not a faster poll, is what removes the lag.
- **Disable the poll (`0`)** — rejected: removes the backstop for missed deliveries + live drift (above).

## Implementation (the shape)

```
GitHub push ──▶ Cloudflare edge ──▶ cloudflared (tunnel)
                                      │  match hostname=argocd.devandre.sbs  path=/api/webhook
                                      │  rewrite Host → argocd.10.0.0.200.nip.io   (SNI same)
                                      ▼
                             ingress-nginx  ──(Host matches the ArgoCD Ingress)──▶  argocd-server /api/webhook
                                      │  HMAC-validate vs argocd-secret webhook.github.secret
                                      ▼
                             refresh apps whose source = minicloud-gitops @ the pushed ref  (seconds)

   (independently) application-controller reconcile loop every 1h = backstop (missed webhook / live drift)
```

- **Webhook:** GitHub hook `650892120` on `andrelair-platform/minicloud-gitops` → `https://argocd.devandre.sbs/api/webhook`, `push` events, content-type json, secret set on both sides.
- **The `configs.cm` SSA gotcha (important for operating this):** the `timeout.reconciliation` change is a
  `configs.cm:` value, and the Helm **CSA** manager owns `argocd-cm`'s `.data`, so an ArgoCD **SSA** sync
  does **not** propagate it (the app sits OutOfSync on `argocd-cm` with the live value unchanged). Apply it
  with a **direct `kubectl patch`** (the `ops-runbooks.md` runbook), then the live value matches Git and
  selfHeal won't fight it. A field change also needs the **application-controller** to re-read it → rollout-restart the statefulset.

## How to operate / verify
```bash
# Webhook reachable + scoped (public):
/usr/bin/curl -s -o /dev/null -w '%{http_code}\n' -X POST https://argocd.devandre.sbs/api/webhook \
  -H 'Content-Type: application/json' -H 'X-GitHub-Event: push' -d '{}'   # → 400 (handler alive, rejects unsigned)
/usr/bin/curl -s -o /dev/null -w '%{http_code}\n' https://argocd.devandre.sbs/                    # → 404 (UI still off the tunnel)

# Reconciliation value live:
ssh controller "kubectl get cm argocd-cm -n argocd -o jsonpath='{.data.timeout\.reconciliation}'"   # → 1h

# Apply a configs.cm change (the SSA gotcha — after the helm-values PR merges):
ssh controller "kubectl patch configmap argocd-cm -n argocd --type merge -p '{\"data\":{\"timeout.reconciliation\":\"1h\"}}'"
ssh controller "kubectl rollout restart statefulset/argo-cd-argocd-application-controller -n argocd"

# Proof of instant sync (observed 2026-10-18): a merge push → argocd-server logs
#   'refreshing app <x> from webhook' ~11s later; GitHub delivery = 200 OK.
ssh controller "kubectl logs deploy/argo-cd-argocd-server -n argocd --since=5m | grep -i 'from webhook'"
```

## Failure modes
- **Tunnel/cloudflared down** → webhook deliveries fail; latency degrades to ≤1h (the poll) — **not an outage**.
- **Forged/unsigned POST** → `400` (HMAC rejects it); only `/api/webhook` is public, nothing else.
- **A `configs.cm` edit "doesn't take"** → the SSA gotcha; `kubectl patch` + controller restart (above).

## Delivery (PRs)
#1872 (tunnel route) · #1873 (Host rewrite — the fix) · #1874 (verification push, reverted by #1875) ·
#1876 (`timeout.reconciliation` 180s→1h).

Related: `ops-runbooks.md` (Cloudflare tunnel recipe + the argocd-cm patch gotcha), `docs/dns-naming-and-externaldns.md`
(the three access planes / tier ①), `.claude/rules/gitops.md` (git-gated auto-sync), memory
`feedback_cloudflared_nip_only_ingress_hosthdr` (the nip.io-only-Ingress Host-rewrite gotcha).
