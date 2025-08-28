#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CERT="${1:-server_cert.pem}"
KEY="${2:-server_key.pem}"
# Prefer explicit KYBER_SK; fallback to FORITECH_SK; fallback to default key
KYBER_SK="${KYBER_SK:-${FORITECH_SK:-$HOME/.foritech/keys/kyber768_sec.bin}}"

if [[ ! -f "$CERT" || ! -f "$KEY" ]]; then
  echo "Missing cert/key. Usage: scripts/demo_run_server.sh [cert] [key]" >&2
  exit 2
fi

exec python3 scripts/tls_pqc_server.py \
  --host 0.0.0.0 --port 8443 \
  --cert "$CERT" \
  --key  "$KEY" \
  --kyber-sk "$KYBER_SK"
