# Diagram-as-Code Standard (mingrammer `diagrams` + Graphviz)

**The constraint (always-on):** architecture **topology posters** and **C4 context/container views** are
written as **Python** (mingrammer [`diagrams`](https://diagrams.mingrammer.com/) + Graphviz) and
regenerated from source — **never hand-placed** in a drawing tool (a hand-drawn SVG/PNG pins every box at
absolute coordinates → drifts + goes stale). Adopted platform-wide 2026-10-17.

## When to use it (and when NOT)
- ✅ **Use `diagrams`** for the whole-platform topology poster + product **C4 context/container** views.
- ❌ **Do NOT replace Mermaid** for in-page flow/sequence/state diagrams (Mermaid-in-Docusaurus stays the
  default, `documentation.md`), and **tbls** stays the tool for **ERDs** (`schema-erd.md`). `diagrams` is
  for the big icon posters, not every diagram.
- This is the one sanctioned place we commit a generated raster/SVG (a code-generated, CI-refreshable
  image is the exception to `project-governance.md`'s "no stale hand-maintained PNGs").
- **Commit both `.png` AND `.svg`**; per-product C4 lives in the **product's own repo** (self-contained),
  the whole-platform diagram in `minicloud-platform-docs/diagrams/`.

## A diagram must COMMUNICATE, not inventory (the quality bar — MANDATORY)
- **Every edge carries a VERB** (fixed vocabulary); **solid = principal flow, dashed = backing dependency**; include a legend.
- **No invented edges** — base every relationship on the **actual manifests/config** (verify in `minicloud-gitops`), mark inferred ones.
- **Light/high-contrast theme**; **ship complementary altitudes** (Capability / Topology / Physical), and mark a logical topology *logical* (capability map ≠ liveness claim — `architecture-views.md`).

> **HOW to do it → the `make-architecture-diagram` skill** (build steps, the icon-fallback helper, vendor-logo
> fetch, the communicate-quality details with the known-wrong-edges list, the refresh CI, and the gotchas —
> SVG-not-self-contained, `--body-file`, commitlint). Pulled on demand when building/updating a diagram.

Reference impls: `minicloud-platform-docs/diagrams/src/platform_overview.py` (whole platform) ·
`retrieva/docs/diagrams/retrieva_container.py` (C4, Docusaurus) · `ktayl-core/docs/diagrams/ktayl_core_container.py` (C4, plain-docs).

Related: `documentation.md` (central docs + Mermaid default), `schema-erd.md` (tbls ERD), `architecture-views.md`, `project-governance.md` (SA C4 artefact set), `reusable-scripts.md`.
