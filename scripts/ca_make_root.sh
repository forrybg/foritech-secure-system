#!/usr/bin/env bash
set -euo pipefail

CN="${CN:-Foritech Root CA 2025}"
DAYS="${DAYS:-3650}"
OUT_DIR="${OUT_DIR:-pki/root}"

mkdir -p "$OUT_DIR"

CERT="$OUT_DIR/root.pem"
KEY="$OUT_DIR/root.key"

if ! command -v foritech >/dev/null 2>&1; then
  echo "foritech CLI not found. Activate your venv or add it to PATH." >&2
  exit 2
fi

if [[ -f "$CERT" || -f "$KEY" ]] && [[ "${FORCE:-0}" != "1" ]]; then
  echo "Root CA already exists ($CERT / $KEY). Set FORCE=1 to overwrite." >&2
  exit 1
fi

foritech x509-make-ca --cn "$CN" --cert-out "$CERT" --key-out "$KEY" --days "$DAYS"
chmod 600 "$KEY"
echo "Root CA created:"
echo "  cert: $CERT"
echo "  key : $KEY (0600)"
