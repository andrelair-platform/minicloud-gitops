# mlflow server image with the PostgreSQL driver for its backend-store
# (platform/ai/litellm/36-mlflow.yaml: `mlflow server --backend-store-uri postgresql://…`).
# Reconstructed for the Harbor retirement (docs/harbor-retirement.md) — the original
# `library/mlflow:v2.16.0-psycopg2` was Harbor-only and retention-GC'd, so it's rebuilt to ghcr.
FROM ghcr.io/mlflow/mlflow:v2.16.0
RUN pip install --no-cache-dir psycopg2-binary
