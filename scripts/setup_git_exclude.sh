#!/usr/bin/env bash
set -euo pipefail
# Writes local-only ignore rules to .git/info/exclude (не пипа .gitignore).

EXCL=".git/info/exclude"
mkdir -p .git/info
touch "$EXCL"

add() {
  local pat="$1"
  if ! grep -qxF "$pat" "$EXCL"; then
    echo "$pat" >> "$EXCL"
    echo "added: $pat"
  fi
}

echo "== Appending local excludes to $EXCL =="

# venv / caches
add ".venv/"
add "__pycache__/"
add ".pytest_cache/"

# local third_party builds
add "third_party/"

# generated crypto artifacts
add "*.pem"
add "*.key"
add "*.der"
add "*.crt"
add "*.csr"
add "*.chain"

# wrap outputs / test artifacts
add "*.enc"
add "*.out"
add "*.bin"

# temp backups
add "*.bak"
add "*.bak.*"

echo "Done."
