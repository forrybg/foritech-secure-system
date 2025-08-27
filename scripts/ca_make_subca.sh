#!/usr/bin/env bash
# Create an intermediate (Issuing) CA signed by the Root CA using OpenSSL.
# Output: pki/subca/subca.pem (cert), pki/subca/subca.key (key), pki/subca/subca_chain.pem (subca+root)
set -euo pipefail

SUBCA_CN="${SUBCA_CN:-Foritech Issuing CA 2025}"
SUBCA_DAYS="${SUBCA_DAYS:-1825}"
ROOT_CERT="${ROOT_CERT:-pki/root/root.pem}"
ROOT_KEY="${ROOT_KEY:-pki/root/root.key}"
OUT_DIR="${OUT_DIR:-pki/subca}"

if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL not found in PATH." >&2
  exit 2
fi

if [[ ! -f "$ROOT_CERT" || ! -f "$ROOT_KEY" ]]; then
  echo "Missing Root CA material ($ROOT_CERT / $ROOT_KEY). Run scripts/ca_make_root.sh first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
SUBCA_KEY="$OUT_DIR/subca.key"
SUBCA_CSR="$OUT_DIR/subca.csr"
SUBCA_CRT="$OUT_DIR/subca.pem"
SUBCA_CHAIN="$OUT_DIR/subca_chain.pem"
CNF="$OUT_DIR/subca_openssl.cnf"

# Minimal OpenSSL config for an Intermediate CA (CA:TRUE, pathlen:0)
cat > "$CNF" <<'CNF'
[ v3_ca ]
basicConstraints = critical, CA:true, pathlen:0
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
CNF

echo ">> Generating Sub-CA ECDSA key..."
openssl ecparam -name prime256v1 -genkey -noout -out "$SUBCA_KEY" >/dev/null 2>&1
chmod 600 "$SUBCA_KEY"

echo ">> Creating Sub-CA CSR..."
openssl req -new -key "$SUBCA_KEY" -out "$SUBCA_CSR" -subj "/CN=${SUBCA_CN}" >/dev/null 2>&1

echo ">> Signing Sub-CA with Root..."
openssl x509 -req -in "$SUBCA_CSR" -CA "$ROOT_CERT" -CAkey "$ROOT_KEY" -CAcreateserial \
  -out "$SUBCA_CRT" -days "$SUBCA_DAYS" -extfile "$CNF" -extensions v3_ca >/dev/null 2>&1

cat "$SUBCA_CRT" "$ROOT_CERT" > "$SUBCA_CHAIN"

echo "Sub-CA created:"
echo "  key   : $SUBCA_KEY (0600)"
echo "  cert  : $SUBCA_CRT"
echo "  chain : $SUBCA_CHAIN   (subca + root)"
