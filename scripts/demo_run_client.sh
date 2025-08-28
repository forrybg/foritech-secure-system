#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

HOST="${1:-127.0.0.1}"
PORT="${2:-8443}"

exec python3 scripts/tls_pqc_client.py --host "$HOST" --port "$PORT"
