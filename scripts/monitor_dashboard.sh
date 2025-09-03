#!/usr/bin/env bash
set -euo pipefail
INTERVAL="${1:-10}"
while true; do
  clear
  date -Is
  echo "== metrics =="
  cat /tmp/foritech-exporter/metrics.prom || echo "(missing)"
  echo
  echo "== last 10 log lines =="
  tail -n 10 logs/monitor.log 2>/dev/null || true
  sleep "$INTERVAL"
done
