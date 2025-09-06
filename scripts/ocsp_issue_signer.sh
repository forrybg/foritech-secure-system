#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CONF="pki/openssl-subca.cnf"
mkdir -p pki/ocsp
# ключ
openssl genrsa -out pki/ocsp/ocsp.key 2048
# CSR
openssl req -new -key pki/ocsp/ocsp.key -subj "/CN=Foritech OCSP" -out pki/ocsp/ocsp.csr
# разширения за OCSPSigning
EXT=$(mktemp); cat > "$EXT" <<'EXT'
basicConstraints=CA:FALSE
keyUsage=nonRepudiation,digitalSignature
extendedKeyUsage=OCSPSigning
EXT
# издаване от Sub-CA
openssl x509 -req -in pki/ocsp/ocsp.csr -CA pki/subca/subca.pem -CAkey pki/subca/subca.key \
  -CAcreateserial -out pki/ocsp/ocsp.pem -days 365 -sha256 -extfile "$EXT"
rm -f "$EXT"
echo "[OK] OCSP signer ready: pki/ocsp/ocsp.pem"
