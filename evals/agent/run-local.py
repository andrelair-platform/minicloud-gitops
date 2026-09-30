#!/usr/bin/env python3
"""Play 9 Layer 2 — model-based agent-config evals, run ON-PLAN via the Claude Code CLI.

For each case file `evals/agent/*.md` (frontmatter `expect_contains` / `expect_absent`
+ a prompt body), runs `claude -p <prompt>` (which uses the owner's Claude Code plan — NOT
the metered API) and checks the output. This is deliberately manual/local; the deterministic
Layer-1 suite is the CI gate.

Usage:  python3 evals/agent/run-local.py     (or: bash evals/agent/run-local.sh)
"""
import glob
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def parse(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    import yaml
    fm = yaml.safe_load(m.group(1)) if m else {}
    body = re.sub(r"^---\n.*?\n---\n", "", t, count=1, flags=re.S).strip()
    return (fm or {}), body


def main() -> int:
    if not shutil.which("claude"):
        print("claude CLI not found — Layer 2 runs on your Claude Code plan; "
              "install/log in first. (Layer 1 `evals/test_hooks.py` needs nothing.)")
        return 3
    cases = [p for p in sorted(glob.glob(os.path.join(HERE, "*.md")))
             if os.path.basename(p) != "README.md"]
    failures = 0
    for c in cases:
        fm, prompt = parse(c)
        name = fm.get("name", os.path.basename(c))
        print(f"== case: {name} ==")
        out = subprocess.run(["claude", "-p", prompt, "--allowedTools", "Read,Grep,Glob"],
                             capture_output=True, text=True).stdout
        bad = []
        for kw in fm.get("expect_contains", []) or []:
            if kw.lower() not in out.lower():
                bad.append(f"missing expected: {kw!r}")
        for kw in fm.get("expect_absent", []) or []:
            if kw.lower() in out.lower():
                bad.append(f"present but should be absent: {kw!r}")
        if bad:
            failures += 1
            print("  FAIL")
            for b in bad:
                print(f"    - {b}")
        else:
            print("  ok")
    print(f"\n{len(cases) - failures}/{len(cases)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
