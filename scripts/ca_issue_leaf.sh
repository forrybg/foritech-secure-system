#!/usr/bin/env bash
set -euo pipefail
# Issue a leaf cert signed by the Root CA (SPKI by default).

CN="${CN:-leaf}"
KEM="${KEM:-Kyber768}"
FORMAT="${FORMAT:-spki}"       # spki | raw
DAYS="${DAYS:-825}"

ROOT_CERT="${ROOT_CERT:-pki/root/root.pem}"
ROOT_KEY="${ROOT_KEY:-pki/root/root.key}"
PQC_PUB="${PQC_PUB:-$HOME/.foritech/keys/kyber768_pub.bin}"

OUT_DIR="${OUT_DIR:-pki/issued}"
mkdir -p "$OUT_DIR"

LEAF="$OUT_DIR/${CN}.pem"
CHAIN="$OUT_DIR/${CN}_fullchain.pem"

if ! command -v foritech >/dev/null 2>&1; then
  echo "foritech CLI not found." >&2
  exit 2
fi

if [[ ! -f "$ROOT_CERT" || ! -f "$ROOT_KEY" ]]; then
  echo "Missing root cert/key ($ROOT_CERT / $ROOT_KEY). Run scripts/ca_make_root.sh first." >&2
  exit 1
fi

if [[ ! -f "$PQC_PUB" ]]; then
  echo "Missing PQC public key: $PQC_PUB" >&2
  echo "Tip: foritech keygen --kid demo-k1   (pub will be ~/.foritech/keys/demo-k1_pub.bin)" >&2
  exit 1
fi

foritech x509-issue \
  --cn "$CN" --kem "$KEM" --format "$FORMAT" \
  --pqc-pub "$PQC_PUB" \
  --ca-cert "$ROOT_CERT" --ca-key "$ROOT_KEY" \
  --cert-out "$LEAF" --days "$DAYS" --chain-out "$CHAIN"

echo "Leaf issued:"
echo "  cert    : $LEAF"
echo "  fullchain: $CHAIN"
