#!/usr/bin/env bash
set -euo pipefail
# Usage: scripts/ca_issue_from_subca.sh "<CN>" "<PQC_PUB_PATH>" [spki|raw]
CN="${1:-leaf-sub1}"
PQC_PUB="${2:-$HOME/.foritech/keys/kyber768_pub.bin}"
FMT="${3:-spki}"

SUB_PEM="pki/subca/subca.pem"
SUB_KEY="pki/subca/subca.key"
ROOT_PEM="pki/root/root.pem"
OUT_LEAF="pki/issued/${CN}.pem"
OUT_CHAIN="pki/issued/${CN}_chain.pem"          # leaf + Sub-CA
OUT_FULL="pki/issued/${CN}_fullchain.pem"       # leaf + Sub-CA + Root

if [ ! -f "$SUB_PEM" ] || [ ! -f "$SUB_KEY" ]; then
  echo "ERR: Missing Sub-CA at $SUB_PEM / $SUB_KEY. Run scripts/ca_make_subca.sh first." >&2
  exit 1
fi
if [ ! -f "$ROOT_PEM" ]; then
  echo "ERR: Missing Root at $ROOT_PEM." >&2
  exit 1
fi
if [ ! -f "$PQC_PUB" ]; then
  echo "ERR: Missing PQC pubkey at $PQC_PUB." >&2
  exit 1
fi

echo ">> Issuing leaf '$CN' from Sub-CA (format=$FMT)..."
foritech x509-issue --cn "$CN" --kem Kyber768 --format "$FMT" \
  --pqc-pub "$PQC_PUB" \
  --ca-cert "$SUB_PEM" --ca-key "$SUB_KEY" \
  --cert-out "$OUT_LEAF" --chain-out "$OUT_CHAIN"

cat "$OUT_CHAIN" "$ROOT_PEM" > "$OUT_FULL"
echo "OK: leaf=$OUT_LEAF"
echo "OK: chain=$OUT_CHAIN (leaf+subca)"
echo "OK: fullchain=$OUT_FULL (leaf+subca+root)"
