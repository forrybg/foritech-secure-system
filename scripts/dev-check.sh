#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate 2>/dev/null || true

echo ">>> Import check"
python3 - <<'PY'
import foritech, sys
print("foritech from:", foritech.__file__)
import foritech.cli.main as m
print("cli import: OK")
PY

echo ">>> CLI check"
foritech --help >/dev/null

echo ">>> Tests"
pytest -q
