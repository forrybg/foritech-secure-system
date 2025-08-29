#!/usr/bin/env bash
set -euo pipefail

# Проста проверка на healthz + Prometheus textfile gauge (pqc_up).
# ENV/args:
#   HOST (default 127.0.0.1)
#   PORT (default 8443)
#
# Примери:
#   scripts/monitor_health.sh
#   HOST=192.168.5.9 PORT=8443 scripts/monitor_health.sh
#
# Изход:
#   - Лог: logs/monitor.log
#   - Метрики: /tmp/foritech-exporter/metrics.prom
# Винаги връща код 0 (за да не шумят timer-и/cron).

HOST="${HOST:-${1:-127.0.0.1}}"
PORT="${PORT:-${2:-8443}}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
MET_DIR="/tmp/foritech-exporter"
MET_FILE="$MET_DIR/metrics.prom"

mkdir -p "$LOG_DIR" "$MET_DIR"

ts() { date +'%Y-%m-%dT%H:%M:%S%z'; }

STATUS=0
BODY="$(curl -k --silent --max-time 3 "https://${HOST}:${PORT}/healthz" || true)"
if [[ "$BODY" == "OK" ]]; then
  STATUS=1
fi

# Prometheus textfile gauge
{
  echo '# HELP pqc_up 1 when demo is healthy, 0 otherwise'
  echo '# TYPE pqc_up gauge'
  echo "pqc_up ${STATUS}"
} > "$MET_FILE"

# Лог
if [[ $STATUS -eq 1 ]]; then
  echo "$(ts) OK host=${HOST} port=${PORT}" >> "$LOG_DIR/monitor.log"
else
  echo "$(ts) FAIL host=${HOST} port=${PORT} body='${BODY}'" >> "$LOG_DIR/monitor.log"
fi

exit 0
