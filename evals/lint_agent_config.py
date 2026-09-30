#!/usr/bin/env python3
"""Deterministic linter for the agent operating config (Play 9, free — no model calls).

Catches a malformed / drifted agent config before it merges:
  * every .claude/skills/*/SKILL.md has valid frontmatter with name + description
  * every .claude/commands/*.md frontmatter parses
  * .claude/settings.json is valid JSON and every hook `command` points at an existing
    script under .claude/hooks/
  * every referenced hook script exists and is syntactically importable (py_compile)

Pure stdlib + PyYAML (frontmatter). Runs in CI on every `.claude/**` change.
Usage:  python3 evals/lint_agent_config.py   # exit 0 clean, 1 on any problem
"""
import glob
import json
import os
import py_compile
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(ROOT, ".claude")


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        t = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        return None
    import yaml
    return yaml.safe_load(m.group(1))


def main() -> int:
    problems = []

    # skills
    skills = glob.glob(os.path.join(CLAUDE, "skills", "*", "SKILL.md"))
    for s in skills:
        fm = frontmatter(s)
        rel = os.path.relpath(s, ROOT)
        if fm is None:
            problems.append(f"{rel}: no frontmatter")
        elif not (isinstance(fm, dict) and fm.get("name") and fm.get("description")):
            problems.append(f"{rel}: frontmatter missing name/description")
    print(f"skills: {len(skills)} found")

    # commands
    cmds = glob.glob(os.path.join(CLAUDE, "commands", "*.md"))
    for c in cmds:
        rel = os.path.relpath(c, ROOT)
        try:
            frontmatter(c)  # just needs to parse
        except Exception as exc:
            problems.append(f"{rel}: frontmatter parse error: {exc}")
    print(f"commands: {len(cmds)} found")

    # settings.json + hook references
    settings_path = os.path.join(CLAUDE, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, encoding="utf-8") as fh:
                settings = json.load(fh)
        except Exception as exc:
            problems.append(f".claude/settings.json: invalid JSON: {exc}")
            settings = {}
        referenced = re.findall(r"\.claude/hooks/([\w.-]+)",
                                json.dumps(settings.get("hooks", {})))
        for script in set(referenced):
            p = os.path.join(CLAUDE, "hooks", script)
            if not os.path.exists(p):
                problems.append(f"settings.json references missing hook: {script}")
        print(f"settings.json: references {len(set(referenced))} hook script(s)")
    else:
        print("settings.json: none (skip)")

    # every hook script compiles
    hooks = glob.glob(os.path.join(CLAUDE, "hooks", "*.py"))
    for h in hooks:
        try:
            py_compile.compile(h, doraise=True)
        except py_compile.PyCompileError as exc:
            problems.append(f"{os.path.relpath(h, ROOT)}: does not compile: {exc}")
    print(f"hooks: {len(hooks)} script(s) compile-checked")

    print()
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("agent config OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
