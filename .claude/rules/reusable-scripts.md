# Reusable Scripts — commit them, don't abandon them in /tmp

When a task produces a script, **decide its lifespan before writing it** and put it where that
lifespan belongs. The failure mode this rule prevents: writing a genuinely reusable helper into
`/tmp`, running it once, and walking away — so the next session (or the next app that needs the same
thing) re-derives it from scratch, slightly differently, with no review and no history.

## The litmus test (apply every time you're about to write a script)

> **Would I, the owner, or another session plausibly run this again — for another app, another
> environment, or next month?**

- **Yes → it's reusable → it MUST be committed** to the owning repo (versioned, reviewed, discoverable).
- **No → it's throwaway scratch → `/tmp` is fine** (and clean it up — see `ops-runbooks` /tmp hygiene).

If you're unsure, it's reusable. Bootstrap/setup/provisioning/migration/verification helpers are
**almost always reusable** even when they feel one-shot ("I'm only creating this OIDC provider once")
— the *next* app needs the same shape, so parameterize and commit it.

## Where committed scripts go — the dividing line (keep `minicloud-gitops` from saturating)

The home is decided by **what the script operates on**, not by which repo you happen to be in:

| The script operates on… | Home | Examples |
|---|---|---|
| **The platform / the controller / the cluster** (Authentik/Vault provisioning, recovery checks, MAAS/power, node ops, systemd units) | **`minicloud-ops/scripts/<area>/`** — the controller-cloned platform-ops repo (has `install.sh`, runs on the controller) | `scripts/authentik/oidc-provider*.sh`, `scripts/bind9-guard.py`, `scripts/maas-power-broker.py` |
| **This repo / its own workflow** (GitHub-project board ops, the BMAD bridge, manifest/validation helpers) | `minicloud-gitops/scripts/<area>/` — genuine *repo-ops* for gitops | `scripts/github-project/`, `scripts/bmad-to-github.sh` |
| **An application** (would run in a container or be unit-tested) | the **product's own repo** (`<repo>/scripts/` or its source tree) | dbt runners, app provisioners |
| One-off *data* piped once and never needed again | `/tmp` (throwaway) | a parsed export consumed in the same task |

**The test:** does it act on the *cluster/controller* (→ `minicloud-ops`) or on *this repo's own process*
(→ `minicloud-gitops/scripts`)? Authentik/Vault bootstrap acts on the platform → `minicloud-ops`, even
though the app it provisions is deployed from gitops. This keeps `minicloud-gitops` to **deployment config**
(`conventions.md`) and stops it accreting every ops helper. Do **not** spin up a *third* "scripts" repo —
`minicloud-ops` already is the reusable-platform-ops home; a new one just fragments ops tooling.

Group by area (`scripts/authentik/`, `scripts/github-project/`, …), matching the existing layout.
`minicloud-ops` is controller-cloned (`~/minicloud-ops`) **and** mirrored on the Mac
(`~/Developer/cloudplateform/minicloud-ops`); edit+commit on the Mac (GPG-signed), `git pull` on the controller.

## Rules for a committed script

1. **Parameterize, don't hardcode** — take app slug / name / URLs via argv or env so it serves every
   future caller, not just today's. A hardcoded-for-one-app script in `scripts/` is half the value.
2. **Header docstring** — one block: what it does, where it runs (e.g. "piped into `ak shell` inside
   the authentik pod"), required inputs, and an example invocation.
3. **No secrets baked in** — read credentials from Vault/ESO/env at runtime; never commit a token or
   a decrypted secret. Break-glass steps reference the mechanism (age/Vaultwarden), they don't embed it.
4. **Idempotent where it can be** — `get_or_create` / check-before-write, so re-running is safe.
5. **Linter noise from out-of-tree imports is expected** — a script that runs inside another image
   (Django `ak shell`, a job container) will fail local Pyright import resolution; add a top-of-file
   `# pyright: reportMissingImports=false` (or equivalent) with a comment saying where it really runs.

## Don't

- Don't write a reusable helper to `/tmp` and move on "to save a step" — committing it *is* the step.
- Don't inline a 40-line provisioning blob into a single `Bash` call when it will be needed again —
  extract it to `scripts/` and call it.
- Don't duplicate an existing helper because the committed one was hard to find — search `scripts/`
  first; extend/parameterize the existing one.

Related: `conventions.md` (deploy-repo vs code-repo), `ops-runbooks` (/tmp hygiene),
`agentic-guardrails.md` (`guard-write.py` blocks committing secret material).
