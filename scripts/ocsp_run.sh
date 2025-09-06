#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${1:-2560}"
openssl ocsp -port "$PORT" -text \
  -rkey pki/ocsp/ocsp.key -rsigner pki/ocsp/ocsp.pem \
  -CA pki/subca/subca.pem -index pki/subca/ca-db/index.txt
