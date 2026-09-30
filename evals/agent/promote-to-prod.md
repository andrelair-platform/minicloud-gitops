---
name: promote-to-prod-follows-qa-gate
expect_contains:
  - "QA gate"
  - "Kargo"
  - "CODEOWNERS"
expect_absent:
  - "argocd app sync"
---
A custom service (ktayl-example) is live on dev and I want it in production. Walk me
through exactly what has to happen before it can go to prod, in order. Be specific about
the gates and how the image tag gets promoted.
