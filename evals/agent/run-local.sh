#!/usr/bin/env bash
# Play 9 Layer 2 — model-based agent-config evals, ON-PLAN via Claude Code (no metered API).
# Thin wrapper around run-local.py so the entry point is a familiar `.sh`.
set -uo pipefail
cd "$(dirname "$0")"
exec python3 ./run-local.py "$@"
