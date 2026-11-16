# Capability Register — register every system you build or adopt (MANDATORY)

The **capability register** `minicloud-platform-docs/data/capability-register.csv` is the single
source of truth for the ktayl Information System's capabilities **and** the systems that run it.
Keeping it current is a **standing rule, not a one-off backfill**: every time a tool becomes a
running part of the platform, it gets a row — **in the same change that deploys it**.

## The rule

> **When you build or adopt a tool that gets deployed, add its row to
> `minicloud-platform-docs/data/capability-register.csv` as part of the same unit of work.**
> Vendor/third-party → a `SYS-` row. Custom-built (your source) → an `APP-` row. A tool you retire
> → keep its row and set `Lifecycle = DECOMMISSIONED` (a cut-over trace, never a silent delete).

This is **deployment-triggered**, not repo-triggered: adding a new upstream Helm chart, a raw-manifest
app, a GAP wrapper chart, or a vendor component **bundled** inside another app all count — if it runs,
it is a system and it needs a row.

## Three pillars (the `L0` column + `Capability ID` prefix)

| `L0` pillar | ID prefix | One row = | `Sourcing Strategy` |
|---|---|---|---|
| **Industrial Insurance Enterprise** | `CAP-###` | a **business capability** (a *need*) | — |
| **Platform & Technical Services** | `SYS-###` | a **vendor / third-party system** | `ADOPT` |
| **Custom Solutions (ktayl IS build)** | `APP-###` | a **built-in-house system** (deployed) | `BUILD` |

**Capability ≠ system.** A capability is a need; a system is a thing that runs. A system realises one or
more capabilities; a capability may map to several systems or none (a GAP). Never fold a vendor/custom
system into a `CAP-` row, and never invent a capability for a tool. Use the next free number in the
pillar's sequence.

## Minimum columns to fill on a `SYS-`/`APP-` row

`Capability ID` · `L0` (the pillar) · `L1 Domain` (role group) · `L3 Capability` (the system name) ·
`Owner` · `Current Application` (name + version/stack) · `Application Type` · `Vendor`
(upstream project, or `In-house (ktayl build)`) · `Criticality` · `DORA` ·
`Application Deployment Status` (`Deployed`/`Decommissioned`/`Demo`) · `Repository` ·
`Declared Environment` (`dev`/`dev+prod`/`prod`/off-cluster) · `Evidence Basis` · `Verified Date` ·
`Sourcing Strategy` (`ADOPT`/`BUILD`) · `Technology Direction` · `Deployment Model`
(`Helm chart (upstream)` / `Raw manifest` / `Wrapper chart` / `Custom image` / `Bundled in <app>`) ·
`Database / Storage` · `Application Lifecycle` · `Evidence Reference` (the gitops path) · `Provenance` ·
`Gap / Decision` (put the product-board ref **here**, e.g. `board #3`). Business-only columns
(LOB/Coverage/Territory/scores) stay empty.

## Generator-safety (do not skip)

Leave **`Product Board` EMPTY** on every `SYS-`/`APP-` row — record the board in `Gap / Decision`
instead. `scripts/gen-si-delivery.py` rolls up per-board maturity by counting `#N` in the
`Product Board` column; a populated value would inflate a board's capability count with infrastructure.
Only `CAP-` rows carry `Product Board`.

## Honesty rules

- **Deployed-only for `APP-`.** Verify against gitops `apps/**` (+ `platform/**` for bundled/manifest
  apps) before adding a custom row as live. A scaffold/parked repo with no running workload is **not** an
  `APP-` system — it stays represented only by its `CAP-` capability rows until it deploys.
- **Vendor custom-image builds** (e.g. a customised Backstage/Open-WebUI/OnlyOffice image) stay a single
  `SYS-` row — cross-reference the image repo in `Gap / Decision`; do **not** duplicate them as `APP-`.
- **Decommission = keep + mark.** When a system is torn down or folded into another, set
  `Application Deployment Status = Decommissioned`, `Lifecycle = DECOMMISSIONED (<date>)`, and point
  `Target Application` at its successor. The row is the audit trail (useful for DORA RoI reasoning).

## Validate before committing

The file must stay well-formed — **68 columns on every row, no malformed line**:

```bash
python3 - <<'PY'
import csv
rows=list(csv.reader(open('minicloud-platform-docs/data/capability-register.csv',newline='')))
bad=[(i+2,len(r)) for i,r in enumerate(rows[1:]) if len(r)!=len(rows[0])]
print("cols", len(rows[0]), "| rows", len(rows)-1, "| malformed:", bad or "none")
PY
```

## Canonical / cross-refs

- Register + scoring rubric: `minicloud-platform-docs/data/capability-register.csv` +
  `capability-register-scoring-guide.md` (§0 documents the three pillars). Consumed by
  `scripts/gen-si-delivery.py` (the SI Delivery Board).
- The register is the authoritative system inventory — keep it in step with `repos.md`
  (repo↔product map), `documentation-standard.md`, and the new-repo checklist in `conventions.md`.
- Scale with the delivery path (`bmad-compliance.md`): a Path-A one-liner that adds no new running
  system needs no register change; standing up / retiring a deployed tool always does.
