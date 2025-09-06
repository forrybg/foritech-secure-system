#!/usr/bin/env bash
# Създава нов Sub-CA, обновява chain-а, оставя стария валиден за overlap прозорец
set -euo pipefail
cd "$(dirname "$0")/.."
NEWCN="${1:-Foritech Issuing CA 2}"
openssl ecparam -name prime256v1 -genkey -noout -out pki/subca/${NEWCN}.key
openssl req -new -key pki/subca/${NEWCN}.key -subj "/CN=${NEWCN}" -out pki/subca/${NEWCN}.csr
openssl x509 -req -in pki/subca/${NEWCN}.csr \
  -CA pki/root/root.pem -CAkey pki/root/root.key -CAcreateserial \
  -out pki/subca/${NEWCN}.pem -days 365 -sha256 \
  -extfile <(printf "basicConstraints=CA:TRUE,pathlen:0\nkeyUsage=keyCertSign,cRLSign")
echo "[OK] New Sub-CA: pki/subca/${NEWCN}.pem"
echo ">> Re-issue leafs with 'scripts/ca_rotate_leaf.sh <cn>' to move traffic gradually."
