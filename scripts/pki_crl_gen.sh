#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CONF="pki/openssl-subca.cnf"
OUT="pki/bundles/issuing.crl.pem"
mkdir -p pki/bundles
openssl ca -config "$CONF" -gencrl -out "$OUT" -batch
echo "[OK] CRL written to $OUT"
