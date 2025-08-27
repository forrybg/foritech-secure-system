#!/usr/bin/env bash
set -euo pipefail

echo "== Secret scan =="
if ! command -v trufflehog >/dev/null 2>&1; then
  echo "trufflehog not found."
  echo "Install with one of:"
  echo "  pipx install trufflehog"
  echo "  # or inside current venv:"
  echo "  pip install trufflehog"
  exit 2
fi

set +e
trufflehog filesystem . --no-update --only-verified --fail
code=$?
set -e
if [ "$code" -eq 0 ]; then
  echo "No verified secrets found. ✅"
else
  echo "Potential secrets detected (exit=$code). Review above. ⚠️"
  exit "$code"
fi
