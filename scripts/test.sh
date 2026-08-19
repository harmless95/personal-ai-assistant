#!/usr/bin/env bash
set -euo pipefail

echo "Running tests..."
uv run pytest -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=json:coverage.json \
  --cov-report=html:htmlcov \
  --junitxml=pytest.xml \
  --no-cov-on-fail | tee pytest-coverage.txt

echo "Tests completed successfully!"
