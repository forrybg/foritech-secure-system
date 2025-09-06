#!/usr/bin/env bash
# Преиздава нов leaf от текущия Sub-CA; обновява bundles/
set -euo pipefail
cd "$(dirname "$0")/.."
CN="${1:-leaf-$(date +%Y%m%d)}"
PUB="${2:-$HOME/.foritech/keys/kyber768_pub.bin}"
OUT="pki/issued/${CN}.pem"
CHAIN="pki/issued/${CN}_fullchain.pem"

foritech x509-issue --cn "$CN" --kem Kyber768 --format spki \
  --pqc-pub "$PUB" \
  --ca-cert pki/subca/subca.pem --ca-key pki/subca/subca.key \
  --cert-out "$OUT" --chain-out "$CHAIN"

mkdir -p pki/bundles
cp "$CHAIN" pki/bundles/fullchain.pem
awk '/BEGIN CERTIFICATE/{n++} n==1{print}' "$CHAIN" > pki/bundles/leaf+issuing.pem
awk '/BEGIN CERTIFICATE/{n++} n==2{print}' "$CHAIN" > pki/bundles/issuing-only.pem

echo "[OK] New leaf: $OUT"
echo "[OK] Bundles updated in pki/bundles/"
