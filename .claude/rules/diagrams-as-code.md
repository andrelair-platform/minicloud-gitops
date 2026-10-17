# Diagram-as-Code Standard (mingrammer `diagrams` + Graphviz)

Architecture **topology posters** and **C4 container views** are written as **Python** and rendered
by [mingrammer **`diagrams`**](https://diagrams.mingrammer.com/) on top of Graphviz — never hand-placed
in a drawing tool. Adopted platform-wide 2026-10-17. Method adapted from the freeCodeCamp tutorial
**["How to Create System Design Diagrams using Python"](https://www.freecodecamp.org/news/how-to-create-system-design-diagrams-using-python/)**
(swap its AWS provider nodes for our on-prem stack: `k8s` + `onprem` + `generic` + `programming` + `saas`).

**Why:** a hand-drawn SVG/PNG places every box at absolute pixel coordinates → it drifts on every
change and goes stale (the exact failure that prompted this — the 871-line
`minicloud-platform-docs/static/diagrams/minicloud-production-stack.html` poster). Diagram-as-code
regenerates the same picture from a short `.py`: edit, `make generate`, commit.

## When to use it (and when NOT)

- ✅ **Use `diagrams`** for: the whole-platform topology poster, and **C4 context/container** views of a
  product (vendor-icon boxes, clusters = layers/boundaries, labelled flows).
- ❌ **Do NOT replace Mermaid** for in-page docs. **Mermaid-in-Docusaurus stays the default** for small
  flow/sequence/state diagrams rendered live in a page (`documentation.md`), and **tbls** stays the tool
  for **ERDs** (`schema-erd.md`). `diagrams` is for the big icon posters, not every diagram.
- This is the one place we commit a generated **raster/SVG** image (the "diagrams over prose, never
  stale PNGs" guidance in `project-governance.md` is about *hand-maintained* PNGs — a code-generated,
  CI-refreshable image is the sanctioned exception).

## Where the source + output live

- **Central tooling + the whole-platform diagram:** `minicloud-platform-docs/diagrams/`
  (`requirements.txt`, `Makefile`, `src/_theme.py`, `src/platform_overview.py`, `fetch-icons.sh`,
  `src/icons/`). Output → `minicloud-platform-docs/static/img/architecture/*.{png,svg}`.
- **Per-product C4 diagrams live in the PRODUCT's OWN repo** (each product owns its docs — see
  `github-projects.md` / `conventions.md`), **not** central. Self-contained: its own
  `<repo>/docs/diagrams/<name>_container.py` + `requirements.txt` + `icons/` + an inlined theme (no
  cross-repo import). Output into that product's docs:
  - Docusaurus product (e.g. **retrieva**): `docs/static/img/architecture/` (served by its site).
  - Plain-`docs/` product (e.g. **ktayl-core**): `docs/architecture/img/`.
- **Commit the generated `.png` AND `.svg`** — GitHub Pages / GitHub README then serve them with **no
  build-time Graphviz dependency**. (Graphviz `dot` is a *system* dependency, never a pip package.)

## How to build one

1. Scaffold from a reference (below). `requirements.txt` = `diagrams>=0.24,<0.25`; system dep
   `brew install graphviz` / `apt-get install -y graphviz`.
2. Model with the **closest real node**: `diagrams.k8s.*`, `diagrams.onprem.*` (groupware/database/
   gitops/registry/security/monitoring/queue/...), `diagrams.programming.{framework,language}`
   (Spring, NextJs, React, Java, NodeJS), `diagrams.saas.*`, `diagrams.generic.*`. `Cluster` = a layer
   or trust boundary; `Edge`/`>>` = labelled flows.
3. **Icon fallback (the key pattern).** ~25 components have no built-in icon (Kargo, KEDA, Longhorn,
   Authentik, Langfuse, LiteLLM, Qdrant, Tailscale, Stripe, …). Use a `node(FallbackClass, label,
   icon="name.png")` helper that renders a vendored PNG from `icons/` if present, else the closest
   **semantic** built-in — the **label is authoritative** (this is how the freeCodeCamp tutorial uses
   the library). Upgrade fidelity by dropping a PNG in `icons/`; no code change.
4. **Vendor logos** with `fetch-icons.sh`: **GitHub org avatars** (`https://github.com/<org>.png?size=256`)
   + **CNCF artwork** raw PNGs (`raw.githubusercontent.com/cncf/artwork/main/projects/<p>/icon/color/...`).
   Best-effort + idempotent; a failed download keeps the fallback.
5. `Diagram(..., outformat=["png","svg"], show=False, graph_attr=…)` writing to the docs static tree.
   Embed the **SVG** in docs pages, the **PNG** in READMEs (always renders on GitHub).

## Edge semantics, accuracy & legibility (MANDATORY — a diagram must *communicate*, not inventory)

A senior review (2026-10-17) found the platform poster read as a "technology inventory with wires." The
fixes are now the standard:

- **Every edge carries a VERB** from a fixed vocabulary — a line must *mean* something specific:
  `provisions · configures · reconciles · builds · pushes · promotes(CODEOWNERS PR) · supplies-secrets ·
  issues-certs · routes-traffic · authenticates · scrapes · ships-logs/traces · backs-up · scales ·
  routes-to-LLM`. **Solid arrow = principal control/data flow · dashed = backing dependency.** Put this in
  a **legend** on the page (boundaries, arrow meaning, statuses).
- **Accuracy — no invented edges.** Base every relationship on the **actual manifests/config/source**
  (verify in `minicloud-gitops`), not on what "usually" connects. Edges found wrong in the audit (learn
  from them): `ESO → ArgoCD` is **inverted** (it's Vault→ESO→*writes Secret*→workloads; ArgoCD only
  *deploys the ExternalSecret CR*); `Longhorn → MinIO` is false (**Velero backs up to** MinIO, which is
  **OFF-CLUSTER on the controller** `10.0.0.1:9000`, + R2); `MetalLB` is **removed** (**Cilium** provides
  CNI *and* the LB IP `10.0.0.200`); Cilium/Gatekeeper/Falco are **cluster-wide substrates**, not edges to
  one node; alert sink is **SES email + Slack**. Mark inferred/unverified edges as such.
- **Legibility — prefer a LIGHT / high-contrast theme** for platform diagrams (`_theme.py` is light: white
  bg, dark text, bold coloured solid/dashed edges, ≥13pt node fonts). Dark backgrounds hide thin dashed
  edges + small labels and print badly. Icons pop on white.
- **Altitude — ship complementary views, don't cram one poster:** a **Capability view** (Mermaid, ~8–12
  groups + principal flows — "understand in 30s"), the **detailed Technology Topology** (mingrammer icons —
  reference), and a **Physical/Deployment view** (nodes · roles · placement · replication · failure
  domains). Keep the **logical** topology marked *logical* (a capability map, not a liveness claim — see the
  maturity-vs-runtime axes in `architecture-views.md`).

## CI

A **regenerate-and-open-a-bot-PR-on-change** workflow (central:
`minicloud-platform-docs/.github/workflows/update-architecture-diagrams.yml`), mirroring the ERD-index
pattern — **NOT a hard blocking gate**: Graphviz output is **not byte-identical across `dot` versions**,
so a strict gate flakes on coordinate noise. **Merge the first bot refresh once** to make CI's render
canonical → the loop converges (no more noise). `make check` is a *local same-environment* drift check.

## Gotchas (proven 2026-10-17)

- **`gh pr create --body "…"` runs backtick command-substitution** (zsh/bash double quotes execute
  backticks): any `` `path/file.yaml` `` in the body is silently replaced by command output (usually
  empty). Write the PR body to a file and use **`gh pr create --body-file`** (or `--body-file -`).
- **SVGs are NOT self-contained — you MUST inline the icons or the SVG is broken standalone.**
  Graphviz/`diagrams` renders SVG with `<image xlink:href="/abs/local/path/icon.png">` — icons are
  referenced by **filesystem path**, not embedded. The SVG renders only where it was generated and is
  **broken when opened in a browser / on GitHub Pages** (every icon 404s → the poster looks empty), and
  it **leaks the author's local path** into a committed file. Fix: a post-process that rewrites every
  local `xlink:href` to a base64 **data URI** (reusable `embed-svg-images.py`, idempotent), run as the
  last step of `make generate`. Verify `grep -c '/Users/' <svg>` == 0. The **PNG** has no such problem
  (icons are rasterised in) — but prefer the self-contained SVG for crisp zoom; use the PNG in READMEs.
- `diagrams` package has **no `__version__`** attr → use `importlib.metadata.version('diagrams')`.
- `diagrams.custom.Custom` needs a **PNG** (Graphviz won't render an SVG as a node image).
- `https://github.com/cloudflare.png` is **not** a PNG (fails the fetch) — keep the built-in Cloudflare node.
- **retrieva / retrieva-backend enforce husky + commitlint** (`@commitlint/config-conventional`):
  `body-max-line-length=100` (wrap body lines), subject lowercase, no trailing period; and a **required
  `CI Success` check** (even `--admin` can't bypass an *expected* check — wait for CI, then squash-merge).
- Per-product placement ⇒ **one PR per repo** (central + each product); there is no single cross-repo PR.

## Reference implementations

- **Whole platform:** `minicloud-platform-docs/diagrams/src/platform_overview.py` (11 layers, 31 vendored
  logos) → embedded in `docs/developer-platform/production-stack-architecture.md`.
- **C4 container (Docusaurus product):** `retrieva/docs/diagrams/retrieva_container.py` → solution-architecture page + both retrieva READMEs.
- **C4 container (plain-docs product):** `ktayl-core/docs/diagrams/ktayl_core_container.py` → standalone `docs/architecture/c4-container.md` + README.

Related: `documentation.md` (central docs site + Mermaid default), `schema-erd.md` (tbls ERD auto-index),
`project-governance.md` (the SA C4 artefact set), `reusable-scripts.md`.
