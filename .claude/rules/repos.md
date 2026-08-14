do ig

# GitHub Repos & Docs Site

## GitHub Repos (org: `andrelair-platform`)

All repos cloned under `~/Developer/cloudplateform/`:

| Repo                                                                                    | Directory                          | Purpose                                           |
| --------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------- |
| [minicloud-platform-docs](https://github.com/andrelair-platform/minicloud-platform-docs) | `minicloud-platform-docs/`       | Docusaurus docs → GitHub Pages                   |
| [minicloud-ansible](https://github.com/andrelair-platform/minicloud-ansible)             | `minicloud-ansible/`             | Bootstrap, Ansible roles (NOT helm values)        |
| [minicloud-backstage](https://github.com/andrelair-platform/minicloud-backstage)         | `minicloud-backstage/`           | Custom Backstage image source                     |
| [minicloud-opentofu](https://github.com/andrelair-platform/minicloud-opentofu)           | `minicloud-opentofu/`            | MAAS IaC (OpenTofu) — run only on controller     |
| [minicloud-gitops](https://github.com/andrelair-platform/minicloud-gitops)               | `minicloud-gitops/`              | ArgoCD app-of-apps + ALL helm values              |
| [minicloud-open-webui](https://github.com/andrelair-platform/minicloud-open-webui)       | `minicloud-open-webui/`          | Custom Open WebUI (CA cert + French BM25)         |
| [minicloud-onlyoffice](https://github.com/andrelair-platform/minicloud-onlyoffice)       | `minicloud-onlyoffice/`          | Custom OnlyOffice (CA cert + NODE_EXTRA_CA_CERTS) |
| [minicloud-plane](https://github.com/andrelair-platform/minicloud-plane)                 | `minicloud-plane/`               | Go Level 4: Plane API + webhook→NATS + REST      |
| [platform-demo](https://github.com/andrelair-platform/platform-demo)                     | `platform-demo/`                 | Go CI/CD demo service                             |
| [ktayl-solution-web](https://github.com/andrelair-platform/ktayl-solution-web)           | `ktayl-solution-web/`            | Astro + Tailwind public website (7 LOB)           |
| [minicloud-agent](https://github.com/andrelair-platform/minicloud-agent)                 | `minicloud-agent/`               | LangGraph ReAct research agent (model: research-agent) |
| [minicloud-crew-agent](https://github.com/andrelair-platform/minicloud-crew-agent)       | `minicloud-crew-agent/`          | CrewAI 3-agent pipeline (model: deep-research-agent) |
| [minicloud-ops](https://github.com/andrelair-platform/minicloud-ops)                     | controller`~/minicloud-ops` only | Python platform recovery check + systemd services |

## Docs Site (minicloud-platform-docs)

Docusaurus 3.10.0. Auto-deploys to GitHub Pages on push to `main`.

```bash
cd ~/Developer/cloudplateform/minicloud-platform-docs
npm install
npm start          # dev server at localhost:3000
npm run build      # production build (fails on broken internal links)
npm run typecheck
npm run clear      # clear Docusaurus cache
```

`sidebars.ts` lists every page by its **doc ID** (Docusaurus strips numeric prefixes: `02-sso-authentik.md` → ID `sso-authentik`). Pages not listed in `sidebars.ts` are invisible in the nav.

Live site: `https://andrelair-platform.github.io/minicloud-platform-docs/`
