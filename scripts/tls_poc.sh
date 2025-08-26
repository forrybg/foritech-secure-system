#!/usr/bin/env bash
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing $1"; exit 1; }; }
need openssl
need foritech

CA_CERT="ca.pem"
CA_KEY="ca.key"
LEAF_CERT="leaf_spki.pem"
LEAF_KEY="leaf_spki.key"

# 1) Генерирай CA (ако липсва)
if [[ ! -f "$CA_CERT" || ! -f "$CA_KEY" ]]; then
  echo "[+] Generate CA..."
  foritech x509-make-ca --cn "foritech-ca" --cert-out "$CA_CERT" --key-out "$CA_KEY"
fi

# 2) Генерирай leaf с SPKI (ако липсва)
if [[ ! -f "$LEAF_CERT" || ! -f "$LEAF_KEY" ]]; then
  echo "[+] Generate leaf (SPKI)..."
  PUB="$HOME/.foritech/keys/kyber768_pub.bin"
  [[ -f "$PUB" ]] || { echo "Missing Kyber pub at $PUB"; exit 1; }
  # self-signed leaf (достатъчно за PoC). Ако искаш от CA: foritech x509-issue --format spki ...
  foritech x509-make --cn "leaf-spki" \
    --pqc-pub "$PUB" --format spki \
    --cert-out "$LEAF_CERT" --key-out "$LEAF_KEY"
fi

echo "[+] Local check:"
foritech x509-info --in "$LEAF_CERT" || true

echo "[+] Start openssl s_server :4433 (background)..."
openssl s_server -accept 4433 -cert "$LEAF_CERT" -key "$LEAF_KEY" -www -quiet >/dev/null 2>&1 &
srv=$!
sleep 0.8

cleanup() { kill "$srv" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "[+] Fetch server cert via s_client..."
TMP=server_cert.pem
openssl s_client -connect 127.0.0.1:4433 -showcerts < /dev/null 2>/dev/null \
  | awk 'BEGIN{c=0} /BEGIN CERTIFICATE/{c=1} {if(c) print} /END CERTIFICATE/{exit}' > "$TMP"

[[ -s "$TMP" ]] || { echo "ERROR: could not capture server cert"; exit 1; }

echo "[+] Inspect captured cert with foritech:"
foritech x509-info --in "$TMP"

echo "[+] OK"
