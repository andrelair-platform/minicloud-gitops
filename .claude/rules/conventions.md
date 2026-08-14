# Project Conventions

## Container image file naming

Always name the container build file **`Dockerfile`** — never `Containerfile`.

Both names use identical syntax. `Dockerfile` is the universally recognised standard that Docker, Buildah, Podman, and all CI actions accept without a `-f` flag. `Containerfile` adds no value in this stack (no Podman workloads) and surprises contributors.

When referencing the file in Makefile or CI:
```makefile
# Makefile
docker build -f Dockerfile .
```
```yaml
# GitHub Actions
uses: docker/build-push-action@v7
with:
  file: Dockerfile
```

---

## Per-repo static documentation (Docusaurus)

Every custom-built repo gets its own **Docusaurus 3.x site** in a `website/` directory, deployed to GitHub Pages at `https://andrelair-platform.github.io/<repo-name>/`.

### What goes where

| Site | Content |
|---|---|
| `minicloud-platform-docs` (org-wide) | **Overview only** — one page per service/component with a 3-5 line summary, sprint status table, and a link to the repo's own docs site |
| `<repo>/website/` (per-repo) | **Full detail** — architecture, data model (MCD/MLD/MPD), API reference, runbooks, ADRs, sprint docs |

The main docs site is a **map**, not a library. Detailed content lives with the code.

### Setup checklist for every new repo

1. Create `website/` with Docusaurus 3.10.0 — copy config from `ktayl-policy-service/website/` as template
2. Add `website/.gitignore` excluding `.docusaurus/`, `build/`, `node_modules/`
3. Add `.github/workflows/deploy-docs.yml` — triggers on push to `main` when `website/**` changes
4. Enable GitHub Pages via API: `gh api repos/andrelair-platform/<repo>/pages --method POST -f "build_type=workflow"`
5. Add an overview page in `minicloud-platform-docs/docs/<section>/` linking to `https://andrelair-platform.github.io/<repo>/`
6. Update `minicloud-platform-docs/sidebars.ts` — add under the relevant section

### Standard `website/` structure

```
website/
  .gitignore           # excludes .docusaurus/, build/, node_modules/
  package.json         # Docusaurus 3.10.0 + @docusaurus/theme-mermaid@3.10.0
  docusaurus.config.ts
  sidebars.ts
  tsconfig.json
  src/css/custom.css   # same green palette as minicloud-platform-docs
  static/.nojekyll
  docs/
    intro.md           # service overview, stack, sprint map, links
    data-model/        # MCD → MLD → MPD (for services with a DB)
    ...                # ADRs, API reference, runbooks as needed
```

### Deploy workflow (standard, copy verbatim)

```yaml
name: Deploy Docs
on:
  push:
    branches: [main]
    paths: ['website/**']
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: false
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v7
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: website/package-lock.json
      - run: npm ci
        working-directory: website
      - run: npm run build
        working-directory: website
      - uses: actions/upload-pages-artifact@v5
        with:
          path: website/build
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v5
        id: deployment
```

### Mermaid support

Always include `@docusaurus/theme-mermaid@3.10.0` (pin exact version — `^3.10.x` resolves to non-existent versions). In `docusaurus.config.ts`:
```ts
markdown: { mermaid: true },
themes: ['@docusaurus/theme-mermaid'],
```

**MDX gotcha:** curly braces `{...}` in markdown text are evaluated as JavaScript. Use backtick code or HTML entities (`&#123;`) instead of literal `{value1, value2}` in prose.
