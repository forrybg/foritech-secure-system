#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
DB="pki/subca/ca-db"
mkdir -p "$DB/newcerts"
: > "$DB/index.txt"
echo '1000' > "$DB/serial"
echo '1000' > "$DB/crlnumber"
echo "[OK] CA DB initialized at $DB"
