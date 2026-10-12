#!/usr/bin/env python3
"""PreToolUse guard for Write/Edit/MultiEdit — keeps secrets and forbidden files
out of the tree deterministically.

FAIL-OPEN on any parse error (exit 0). Blocks (exit 2) when the incoming content
carries literal secret material, or the target path is one that must never be
hand-edited / committed.

What it blocks + why:
  1. Literal secret material in the new content — private keys, AWS access keys,
     Vault tokens (hvs./hvb.), GitHub PATs, Slack tokens. Secrets belong in Vault
     → ESO, never in a committed file (gitops.md ESO pattern).
  2. Editing a vendored Helm dep under `services/*/helm/charts/` — it is gitignored
     and rebuilt by `helm dependency build`; hand-edits are lost/harmful (gitops.md).
  3. Writing anything under `.git/`.
  4. Creating a `CLAUDE.md` inside this repo — it must NEVER be committed
     (feedback_claude_md_repo_rule). (Hooks are project-scoped, so the workspace-root
     CLAUDE.md outside this repo is unaffected.)
  5. Creating a NEW subdirectory under `manifests/` — it is FROZEN (ARCHITECTURE.md
     FREEZE + remediation-plan.md Stage 6). New config goes to `platform/<layer>/` or
     `is/<group>/`. Edits to files in EXISTING manifests/ subdirs stay allowed (the
     LOT E content moves still operate there).
  6. Creating application source code (`*.py`/`*.go`/`*.ts`) outside the sanctioned
     tooling dirs (`scripts/`, `evals/`, `.claude/`, `.github/`). This is the DEPLOYMENT
     repo, not a code repo — app code lives in the product's own repo (conventions.md
     "deployment repo vs code repo"; ARCHITECTURE.md "No application source code").
"""
import json
import os
import re
import sys

# When run as the `platform-guardrails` plugin, Claude Code sets CLAUDE_PLUGIN_ROOT → name the
# plugin in the block message; otherwise this is the repo's committed .claude/hooks/ copy.
_SOURCE = ("plugin: platform-guardrails (guard-write.py)"
           if os.environ.get("CLAUDE_PLUGIN_ROOT") else ".claude/hooks/guard-write.py")

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"), "a PRIVATE KEY"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key id"),
    (re.compile(r"\bhv[sb]\.[A-Za-z0-9_-]{20,}"), "a Vault token"),
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "a GitHub personal access token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}"), "a GitHub fine-grained PAT"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}"), "a GitLab PAT"),
]

PATH_CHARTS = re.compile(r"/helm/charts/")
PATH_GIT = re.compile(r"(^|/)\.git/")

# The repo root (= project dir when running inside minicloud-gitops). Used to resolve a
# tool_input path to a repo-relative path and to test "does this manifests/ subdir already
# exist?" for the FREEZE check. Fail-open everywhere: if we can't resolve the root, skip.
_PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", "")

# App source code lives in the product repo, NOT this deployment repo. These are the only
# dirs that legitimately hold scripts/code here (ops/CI/agent tooling + evals), verified
# against the current tree (all existing *.py/*.go/*.ts are under exactly these).
_CODE_EXT = (".py", ".go", ".ts")
_CODE_ALLOWED_PREFIXES = ("scripts/", "evals/", ".claude/", ".github/")


def repo_rel(path: str) -> str:
    """Best-effort repo-relative, forward-slashed path; '' if it can't be resolved."""
    if not path:
        return ""
    p = path
    if _PROJECT_DIR:
        root = _PROJECT_DIR.rstrip("/") + "/"
        if p.startswith(root):
            p = p[len(root):]
        elif os.path.isabs(p):
            # absolute but not under the project dir → not our concern
            return ""
    return p.lstrip("/")


def block(msg: str) -> None:
    sys.stderr.write(f"BLOCKED by {_SOURCE}\n" + msg + "\n")
    sys.exit(2)


def incoming_text(tool_input: dict) -> str:
    chunks = []
    if isinstance(tool_input.get("content"), str):
        chunks.append(tool_input["content"])           # Write
    if isinstance(tool_input.get("new_string"), str):
        chunks.append(tool_input["new_string"])         # Edit
    for e in tool_input.get("edits", []) or []:          # MultiEdit
        if isinstance(e, dict) and isinstance(e.get("new_string"), str):
            chunks.append(e["new_string"])
    return "\n".join(chunks)


def main() -> None:
    try:
        data = json.load(sys.stdin)
        ti = data.get("tool_input") or {}
        path = ti.get("file_path", "") or ""
    except Exception:
        sys.exit(0)
    try:
        if PATH_GIT.search(path):
            block("Refusing to write under .git/.")
        if PATH_CHARTS.search(path):
            block("services/*/helm/charts/ is a vendored, gitignored Helm dependency "
                  "rebuilt by `helm dependency build` — do not hand-edit it (gitops.md).")
        if path.rstrip("/").split("/")[-1] == "CLAUDE.md":
            block("CLAUDE.md must NEVER live in a committed repo "
                  "(feedback_claude_md_repo_rule). Put durable context in "
                  ".claude/rules/*.md, AGENTS.md, or the memory system instead.")

        # The next two rules are CREATION-only (new entries) — editing a file that already
        # exists is always allowed (e.g. the LOT E content moves still edit manifests/ files).
        rel = repo_rel(path)
        is_creation = bool(path) and not os.path.exists(path)
        if rel and is_creation:
            # (5) manifests/ is FROZEN — block a NEW manifests/<subdir>. A write into an
            #     already-existing subdir is fine; only brand-new subdirs are refused.
            if rel.startswith("manifests/"):
                parts = rel.split("/")
                if len(parts) >= 2 and _PROJECT_DIR:
                    subdir = os.path.join(_PROJECT_DIR, "manifests", parts[1])
                    if not os.path.isdir(subdir):
                        block("manifests/ is FROZEN — no NEW subdirectories (ARCHITECTURE.md "
                              "FREEZE). Put new config under platform/<layer>/ or is/<group>/ "
                              "and its Argo CD Application under apps/platform/<layer>/ or "
                              "apps/is/<group>/.")
            # (6) no application source code in this deployment repo.
            if rel.endswith(_CODE_EXT) and not rel.startswith(_CODE_ALLOWED_PREFIXES):
                block("minicloud-gitops is the DEPLOYMENT repo — application source code "
                      f"(a {os.path.splitext(rel)[1]} file) belongs in the product's OWN repo "
                      "(conventions.md). Only scripts/, evals/, .claude/, .github/ may hold "
                      "tooling code here; a runtime Job git-clones app code from its repo.")

        text = incoming_text(ti)
        for pat, label in SECRET_PATTERNS:
            if pat.search(text):
                block(f"Refusing to write {label} into a file. Secrets go to Vault "
                      f"→ ESO (ExternalSecret), never committed content (gitops.md).")
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
