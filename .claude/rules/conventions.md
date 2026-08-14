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

---

## Repo standardisation (GitHub About + README + LICENSE)

Every custom-built repo must be fully standardised before merging S001 to `main`. Reference implementation: `ktayl-policy-service`.

### 1. GitHub About panel

Set via `gh api` — do this once when creating the repo:

```bash
# Description, homepage (docs site), topics
gh api repos/andrelair-platform/<repo> \
  --method PATCH \
  -f description="<one-line description of the service>" \
  -f homepage="https://andrelair-platform.github.io/<repo>/"

gh api repos/andrelair-platform/<repo>/topics \
  --method PUT \
  -f 'names[]=go' -f 'names[]=kubernetes' -f 'names[]=microservice' \
  # add service-specific topics: insurance, postgresql, python, etc.
```

**Required fields:**
- `description` — one sentence, no trailing period, mentions the tech stack
- `homepage` — always the GitHub Pages docs URL (`https://andrelair-platform.github.io/<repo>/`)
- `topics` — at minimum: language + `kubernetes` + `microservice`; add domain tags (e.g. `insurance`, `argocd`)

### 2. Required root files

Every repo must have these three files at the root:

| File | Content |
|---|---|
| `README.md` | Full structured README (see template below) |
| `LICENSE` | MIT — copy from `ktayl-policy-service/LICENSE`, update copyright year |
| `CONTRIBUTING.md` | Branch rules, commit style, PR requirements — copy from `ktayl-policy-service/CONTRIBUTING.md` |

### 3. README structure (mandatory sections in order)

```markdown
# <repo-name>

[![CI](https://github.com/andrelair-platform/<repo>/actions/workflows/ci.yml/badge.svg)](...)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![<Language>](https://img.shields.io/badge/<Lang>-<version>-blue)](<lang url>)
[![Supply chain: cosign](https://img.shields.io/badge/supply%20chain-cosign%20signed-green)](https://github.com/sigstore/cosign)

> <one-paragraph italic description — what it does, what platform it runs on, why it matters>

**Live demo:** <URL if publicly accessible>          ← omit if no public URL
**Live docs:** <https://andrelair-platform.github.io/<repo>/>
**Platform docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>

---

## Table of Contents
## <Domain model / Data model>   ← for services with a DB
## Architecture                  ← diagram + component table
## Getting Started               ← prerequisites, run locally, test, build
## CI/CD Pipeline                ← step-by-step + branch strategy + secrets table
## Endpoints                     ← method/path/description table
## Environment variables         ← variable/default/description table
## Database migrations           ← only if applicable
## Contributing
## License
```

**Badges to include:**
- CI badge — always
- License badge — always (MIT yellow)
- Language/framework badge — always (Go blue, Python blue, Node green, etc.)
- cosign badge — always (supply chain green)
- Extra badges optional: version, coverage, etc.

**One-liner description rules:**
- Use `>` blockquote format
- Mention: what it does + platform context (self-hosted k8s / ktayl-solution IS / etc.) + key tech
- No bullet points — single flowing paragraph

**Architecture section must include:**
- ASCII diagram showing CI → ArgoCD → Pod flow
- Component table: Runtime, Router/Framework, Database, Registry, GitOps, Sprint

### 4. Checklist (apply when creating a new repo)

- [ ] `gh api PATCH` — set description + homepage
- [ ] `gh api PUT /topics` — set topics
- [ ] `README.md` — full structure with all mandatory sections
- [ ] `LICENSE` — MIT, correct year
- [ ] `CONTRIBUTING.md` — branch rules, commit style, PR requirements
- [ ] Docusaurus `website/` — see Per-repo static documentation section above
- [ ] GitHub Pages enabled — `gh api repos/.../pages --method POST -f "build_type=workflow"`
- [ ] Release automation — see Automated releases section below

---

## Automated releases (release-please)

Every custom-built repo uses **release-please** to publish GitHub Releases automatically from conventional commits (`feat:` → minor bump, `fix:` → patch bump, `feat!:` → major bump).

### How it works

1. On every push to `main`, the `release.yml` workflow runs release-please
2. release-please opens a **"release PR"** (e.g. `chore: release v1.2.0`) that bumps `version.txt` + updates `CHANGELOG.md`
3. When that PR is merged to `main`, release-please creates the git tag (`v1.2.0`) and a GitHub Release with auto-generated notes

Zero manual steps. The release PR accumulates changes and only merges when you decide to cut a release.

### Required files per repo

**`.github/workflows/release.yml`** (copy verbatim):
```yaml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name:        ${{ steps.release.outputs.tag_name }}
    steps:
      - uses: google-github-actions/release-please-action@v4
        id: release
        with:
          token:         ${{ secrets.GITHUB_TOKEN }}
          config-file:   release-please-config.json
          manifest-file: .release-please-manifest.json
```

**`release-please-config.json`** — adjust `package-name` per repo:
```json
{
  "packages": {
    ".": {
      "release-type": "simple",
      "package-name": "<repo-name>",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "bump-patch-for-minor-pre-major": true
    }
  }
}
```

Use `release-type: node` for Node.js repos (bumps `package.json` version automatically).

**`.release-please-manifest.json`** — tracks current version:
```json
{
  ".": "0.1.0"
}
```

**`version.txt`** — current version string (updated by release-please):
```
0.1.0
```

**`CHANGELOG.md`** — initial file (release-please populates it):
```markdown
# Changelog

All notable changes to <repo-name> are documented here.

This file is maintained by [release-please](https://github.com/googleapis/release-please).
```

### Reference implementation

`ktayl-policy-service` — all 5 files committed, first release created when S003 merged to main.

### Node.js repos

Use `"release-type": "node"` in `release-please-config.json` — release-please will also bump the `version` field in `package.json` automatically. No `version.txt` needed.
