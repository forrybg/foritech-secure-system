#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d-%H%M%S)
DEST="backups/$TS"
mkdir -p "$DEST"

echo "[*] Saving repo HEAD/status/tracked files..."
git rev-parse HEAD > "$DEST/HEAD.txt"
git status --porcelain > "$DEST/status.txt"
git ls-files -z | xargs -0 tar -czf "$DEST/repo-tracked.tar.gz"

echo "[*] Saving keys (~/.foritech/keys)..."
if [ -d "$HOME/.foritech/keys" ]; then
  tar -czf "$DEST/foritech-keys.tar.gz" -C "$HOME" .foritech/keys
else
  echo "(no ~/.foritech/keys)" > "$DEST/foritech-keys.MISSING"
fi

echo "[*] Saving local PKI (./pki)..."
if [ -d "pki" ]; then
  tar -czf "$DEST/pki.tar.gz" pki
else
  echo "(no ./pki)" > "$DEST/pki.MISSING"
fi

echo "[OK] Backup created at: $DEST"
ls -lh "$DEST" || true

echo
echo "Note: 'backups/' is not tracked by git. To hide from 'git status' locally:"
echo "  echo backups/ >> .git/info/exclude"
