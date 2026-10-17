# Architecture Views — the multi-level documentation system (Platform ↔ IS)

The architecture is documented at **multiple abstraction levels**, through **one pillar-neutral entry
point**, so a reader can navigate from enterprise capabilities down to applications, platform
dependencies and deployments **without confusing architectural intent with verified operational
reality**. Established 2026-10-17. Companion rules: `platform-vs-information-system.md` (the boundary),
`diagrams-as-code.md` (the tooling), `documentation.md` (the docs-as-map discipline).

> The problem this solves: a single "everything on the cluster" poster **mixes** Platform capabilities
> and IS business apps and misrepresents ownership. One diagram cannot answer *what the platform
> provides*, *what the IS does*, and *how the IS consumes the platform* — those are three questions at
> three altitudes.

## The levels (each answers a different question)

| View | Altitude | Tool | Lives at |
|---|---|---|---|
| **Architecture Hub** (entry point) | navigation | Markdown | `minicloud-platform-docs/docs/architecture/index.md` — **referenced from BOTH sidebars** (one hub, not duplicated) + linked from `intro.md` |
| **L1 — Enterprise Landscape** | context — Platform ↔ IS relationship (~12 grouped boxes + one `consumes` edge) | **Mermaid** (inline) | in the Hub |
| **L2 — Platform Topology** | detailed technical capabilities (icons) | **mingrammer `diagrams`** | `docs/developer-platform/production-stack-architecture` + `diagrams/src/platform_overview.py` |
| **L2 — IS Application Landscape** | business apps grouped by insurance domain, maturity-coloured | **Mermaid** (inline) | `docs/architecture/is-application-landscape.md` |
| **Platform ↔ IS Dependency Matrix** | the consumption contract | Markdown table | `docs/architecture/platform-is-dependency-matrix.md` |
| **L3 — Deployment / component** (future) | where/how apps run, ADRs | mingrammer / manifests / ADRs | per-product `docs/` |

**Tooling split (don't over-call everything "C4"):** **Mermaid for high-level maps** (inline, live-
rendered, status-coloured, no PNG pipeline) · **mingrammer for the detailed icon topology** (see
`diagrams-as-code.md`). The L1 landscape is *C4-inspired* (a context view); the topology is a
complementary deployment/infrastructure view — label them accurately, not all "C4".

## The non-negotiable principles (encode these in every view)

1. **Ownership ≠ deployment location.** Platform and IS are **logical ownership** boundaries, not
   Kubernetes namespaces. *A Claims app running on k8s is still an IS application.* The platform owns the
   **capability** (Postgres-as-a-service, Authentik SSO, the LLM gateway, the telemetry stack); the IS
   owns the **use** (the data model, the business authz, the AI use case, the business KPIs). A diagram
   must place an app by *who owns it*, never by *where its pod runs*.
2. **Maturity ≠ runtime — two independent axes, never conflated.**
   - **Maturity** (does the code exist?): **Implemented** (real code + substantial functionality) ·
     **Scaffold** (repo/skeleton, little business logic) · **Planned** (no implementation yet).
   - **Runtime** (is it actually running?): **Verified** (checked against the live cluster) ·
     **Unverified** (inferred from GitOps/repo evidence only).
   - **Do NOT claim an app is "live" from the mere existence of its repo or ArgoCD manifest.** If the
     cluster wasn't reached, every status is **Unverified** — say so. (ktayl is a *synthetic enterprise*;
     "implemented" never implies real production usage — `synthetic-enterprise.md`.)
3. **No new source of truth.** The hub + maps are a **navigation/context layer** that **links** the
   authoritative docs (`insurance-platform/enterprise-architecture-blueprint`, `capability-map`, the
   per-app docs) — they never restate them. Selecting a domain leads the reader *toward* its
   authoritative docs + its platform dependencies.
4. **Dependency matrix captures ownership + interfaces, not just arrows:** columns = **Consumer ·
   Provided capability · Interface/contract · Ownership · Maturity · Runtime · Evidence/reference**;
   inferred rows are **marked `unverified`**.
5. **Version-controlled + readable.** Mermaid inline in Markdown; mingrammer sources in `diagrams/src/`.
   Keep each view readable (L1 ~12–15 boxes) — altitude is the tool for legibility, not cramming.

## Gotchas (proven 2026-10-17)

- **Docusaurus doc links from index/category pages:** use the **real filename + `.md`** (incl. the
  numeric prefix, e.g. `../developer-platform/29-production-stack-architecture.md`). Bare slug-form links
  (no `.md`) resolve **unreliably from a category-index page** and fail `onBrokenLinks: 'throw'` (they
  eat into the baseUrl). The category-index route is `/architecture` (no trailing slash).
- **One hub, both sidebars:** define the nav once (`const architectureNav` in `sidebars.ts`) and
  reference it in `platformSidebar` **and** `isSidebar` — a doc may appear in multiple sidebars; don't
  duplicate the content.
- **De-mixing the platform topology:** remove IS-owned workloads (ERPNext/Nextcloud/Matrix/Jitsi/Plane/
  Docuseal/Paperless/n8n/Temporal/Stalwart/Metabase) from the platform diagram, but **keep the data-infra
  engines** (Postgres/CNPG, MariaDB, NATS, Valkey, ClickHouse, Longhorn/MinIO) — the engine is a platform
  capability; the schema/data is IS (shown in the IS map).

## Reference implementation
`minicloud-platform-docs` PR #272: the Hub + L1 (Mermaid) + L2 IS landscape (Mermaid) + dependency matrix
+ the de-mixed `platform_overview.py` L2 topology + the shared-sidebar wiring. Planned follow-up: ADRs
under `docs/architecture/` (*why* ArgoCD/Authentik/Cilium/Longhorn + the Platform/IS split).
