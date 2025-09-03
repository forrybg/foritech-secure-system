#!/usr/bin/env bash
# Usage: scripts/ocsp_check.sh pki/issued/leaf-sub1.pem
set -euo pipefail
cd "$(dirname "$0")/.."
CERT="$1"
openssl ocsp -issuer pki/subca/subca.pem -cert "$CERT" \
  -url http://127.0.0.1:2560 -CAfile pki/root/root.pem -resp_text -noverify
