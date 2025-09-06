#!/usr/bin/env bash
# Употреба:
#   scripts/pki_revoke.sh --cert pki/issued/leaf-sub1.pem
# или по сериен номер:
#   scripts/pki_revoke.sh --serial 01A2...
set -euo pipefail
cd "$(dirname "$0")/.."
CONF="pki/openssl-subca.cnf"

if [[ "${1:-}" == "--cert" ]]; then
  CERT="$2"
  openssl ca -config "$CONF" -revoke "$CERT" -batch
elif [[ "${1:-}" == "--serial" ]]; then
  SERIAL="$2"
  # намираме cert по сериен през индекс
  CERT=$(awk -v s="$SERIAL" '$1=="V" && $4==s {print "pki/subca/ca-db/newcerts/"$4".pem"}' pki/subca/ca-db/index.txt)
  [[ -f "$CERT" ]] || { echo "[!] cert for serial $SERIAL not found"; exit 2; }
  openssl ca -config "$CONF" -revoke "$CERT" -batch
else
  echo "Usage: $0 --cert <path.pem> | --serial <HEX>"
  exit 2
fi

scripts/pki_crl_gen.sh
