#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Usage:
#   scripts/ca_rotate_symlinks.sh <leaf.pem> <leaf.key> <fullchain.pem>
# Defaults are your current leaf-sub1 artifacts under ./pki/issued.
LEAF="${1:-pki/issued/leaf-sub1.pem}"
KEY="${2:-pki/issued/leaf-sub1.key}"
FULLCHAIN="${3:-pki/issued/leaf-sub1_fullchain.pem}"

for f in "$LEAF" "$KEY" "$FULLCHAIN"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing: $f" >&2
    echo "Usage: $0 <leaf.pem> <leaf.key> <fullchain.pem>" >&2
    exit 2
  fi
done

# Optional quick verify if root is present
if [[ -f pki/root/root.pem ]]; then
  echo ">> Verifying chain against root (foritech x509-verify)..."
  if ! foritech x509-verify --leaf "$LEAF" --chain "$FULLCHAIN" --root pki/root/root.pem; then
    echo "verify failed; not rotating symlinks" >&2
    exit 3
  fi
fi

ln -sf "$FULLCHAIN" server_cert.pem
ln -sf "$KEY"       server_key.pem
echo "Symlinks updated:"
echo "  server_cert.pem -> $FULLCHAIN"
echo "  server_key.pem  -> $KEY"
