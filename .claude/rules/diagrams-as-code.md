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

## CI

A **regenerate-and-open-a-bot-PR-on-change** workflow (central:
`minicloud-platform-docs/.github/workflows/update-architecture-diagrams.yml`), mirroring the ERD-index
pattern — **NOT a hard blocking gate**: Graphviz output is **not byte-identical across `dot` versions**,
so a strict gate flakes on coordinate noise. **Merge the first bot refresh once** to make CI's render
canonical → the loop converges (no more noise). `make check` is a *local same-environment* drift check.

## Gotchas (proven 2026-10-17)

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
