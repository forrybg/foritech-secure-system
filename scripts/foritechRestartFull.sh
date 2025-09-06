#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
echo "[i] stop bg helper (if any)"
scripts/server_bg.sh stop 2>/dev/null || true
fuser -k 8443/tcp 2>/dev/null || pkill -f tls_pqc_server.py || true

echo "[i] reset-failed + daemon-reload + enable --now"
sudo systemctl reset-failed foritech-pqc.service || true
sudo systemctl daemon-reload
sudo systemctl enable --now foritech-pqc.service

sleep 1
echo "[i] status"
systemctl status foritech-pqc.service -n 15 --no-pager || true

echo -n "[health] " ; curl -ks https://127.0.0.1:8443/healthz || true ; echo
echo "[log tail]"
journalctl -u foritech-pqc.service -n 30 --no-pager || true
