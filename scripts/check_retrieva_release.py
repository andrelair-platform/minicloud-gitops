#!/usr/bin/env python3
"""Fail when Retrieva's product release omits or drifts a deployable component."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "services/retrieva/release.json"
EXPECTED = {
    "backend": (ROOT / "services/retrieva/helm/values-prod.yaml", ("backend", "image", "tag")),
    "frontend": (ROOT / "services/retrieva/helm/values-prod.yaml", ("frontend", "image", "tag")),
    "assessment-crew": (
        ROOT / "services/retrieva-assessment-crew/helm/values-prod.yaml",
        ("minicloud-app-deployment", "image", "tag"),
    ),
}
TAG = re.compile(r"^[0-9a-f]{7,40}$")
KEY_VALUE = re.compile(r"^(\s*)([A-Za-z0-9_-]+):(?:\s*(.*?))?\s*$")


def scalar_at(path: Path, wanted: tuple[str, ...]) -> str:
    stack: list[tuple[int, str]] = []
    for raw in path.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = KEY_VALUE.match(raw)
        if not match:
            continue
        indent, key, value = len(match.group(1)), match.group(2), match.group(3) or ""
        while stack and stack[-1][0] >= indent:
            stack.pop()
        current = tuple(item[1] for item in stack) + (key,)
        if current == wanted:
            value = value.split("#", 1)[0].strip().strip("\"'")
            if not value:
                raise ValueError(f"{path}: {'.'.join(wanted)} is empty")
            return value
        if not value:
            stack.append((indent, key))
    raise ValueError(f"{path}: missing {'.'.join(wanted)}")


def main() -> int:
    release = json.loads(MANIFEST.read_text())
    components = release.get("components", {})
    errors: list[str] = []
    if set(components) != set(EXPECTED):
        errors.append(
            f"component set must be exactly {sorted(EXPECTED)}; got {sorted(components)}"
        )
    for name, (values_file, yaml_path) in EXPECTED.items():
        declared = components.get(name, {}).get("tag")
        actual = scalar_at(values_file, yaml_path)
        if declared != actual:
            errors.append(f"{name}: release tag {declared!r} != prod values tag {actual!r}")
        if not isinstance(declared, str) or not TAG.fullmatch(declared):
            errors.append(f"{name}: tag must be an immutable hexadecimal SHA, got {declared!r}")

    stage = (ROOT / "services/retrieva/kargo/files/stage-product-prod.yaml").read_text()
    product_dev = (ROOT / "services/retrieva/kargo/files/stage-product-dev.yaml").read_text()
    required_stage_tokens = {
        "backend": ("name: retrieva-backend", "components.backend.tag"),
        "frontend": ("name: retrieva-frontend", "components.frontend.tag"),
        "assessment-crew": (
            "name: retrieva-assessment-crew",
            "components.assessment-crew.tag",
        ),
    }
    for name, tokens in required_stage_tokens.items():
        for token in tokens:
            if token not in stage:
                errors.append(f"product-prod omits {name}: missing {token!r}")
        origin_token = tokens[0]
        if origin_token not in product_dev:
            errors.append(f"product-dev omits {name}: missing {origin_token!r}")

    if stage.count("stages: [product-dev]") != len(EXPECTED):
        errors.append("product-prod must source all three components from product-dev")
    if stage.count("selectionPolicy: MatchUpstream") != len(EXPECTED):
        errors.append("product-prod must match each component to the current product-dev bundle")

    analysis = ROOT / "services/retrieva/kargo/files/analysis-product-dev.yaml"
    if not analysis.exists() or "message/send" not in analysis.read_text():
        errors.append("product-dev must have a live A2A integration AnalysisTemplate")

    for legacy in ("stage-backend-prod.yaml", "stage-frontend-prod.yaml", "stage-crew-prod.yaml"):
        if (ROOT / "services/retrieva/kargo/files" / legacy).exists():
            errors.append(f"legacy independent prod Stage must not exist: {legacy}")

    if errors:
        print("Retrieva product release completeness: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Retrieva product release completeness: PASS (backend + frontend + assessment-crew)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
