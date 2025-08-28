#!/usr/bin/env bash
set -euo pipefail

CN="${1:-Foritech Issuing CA 1}"
ROOT_PEM="pki/root/root.pem"
ROOT_KEY="pki/root/root.key"
SUB_DIR="pki/subca"

if [ ! -f "$ROOT_PEM" ] || [ ! -f "$ROOT_KEY" ]; then
  echo "ERR: Missing root CA at $ROOT_PEM / $ROOT_KEY. Create it first." >&2
  echo "Tip: 'foritech x509-make-ca --cn Foritech Root CA 2025 --cert-out pki/root/root.pem --key-out pki/root/root.key'" >&2
  exit 1
fi

mkdir -p "$SUB_DIR"
SUB_KEY="$SUB_DIR/subca.key"
SUB_CSR="$SUB_DIR/subca.csr"
SUB_PEM="$SUB_DIR/subca.pem"

if [ -f "$SUB_PEM" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "Sub-CA already exists at $SUB_PEM. Set FORCE=1 to overwrite." >&2
  exit 0
fi

echo ">> Generating Sub-CA key (ECDSA P-256)..."
openssl ecparam -name prime256v1 -genkey -noout -out "$SUB_KEY" >/dev/null 2>&1

echo ">> CSR for Sub-CA..."
openssl req -new -key "$SUB_KEY" -subj "/CN=$CN" -out "$SUB_CSR" >/dev/null 2>&1

echo ">> Signing Sub-CA with Root..."
# extfile for CA=true, pathlen:0, KU/AKI/SKI
EXT="$(mktemp)"
cat >"$EXT" <<EOT
basicConstraints=critical,CA:true,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
EOT

openssl x509 -req -in "$SUB_CSR" -CA "$ROOT_PEM" -CAkey "$ROOT_KEY" -CAcreateserial \
  -days 1825 -sha256 -extfile "$EXT" -out "$SUB_PEM" >/dev/null 2>&1
rm -f "$EXT" "$SUB_CSR"

echo "OK: Sub-CA written: $SUB_PEM  (key: $SUB_KEY)"
