#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
echo "[i] reset-failed + daemon-reload + restart"
sudo systemctl reset-failed foritech-pqc.service || true
sudo systemctl daemon-reload
sudo systemctl restart foritech-pqc.service
sleep 1
systemctl status foritech-pqc.service -n 10 --no-pager || true
echo -n "[health] "; curl -ks https://127.0.0.1:8443/healthz || true; echo
