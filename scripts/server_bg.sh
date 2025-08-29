#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# ---- config ----
PY="${PY:-./.venv-clean/bin/python}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8443}"
CERT="${CERT:-pki/issued/tls-demo_fullchain.pem}"
KEY="${KEY:-pki/issued/tls-demo.key}"
KYBER_SK="${KYBER_SK:-${FORITECH_SK:-$HOME/.foritech/keys/kyber768_sec.bin}}"
LOGDIR="${LOGDIR:-logs}"
LOG="${LOG:-$LOGDIR/pqc-server.log}"
PIDFILE="${PIDFILE:-/tmp/pqc-server.pid}"

mkdir -p "$LOGDIR"

cmd=( "$PY" scripts/tls_pqc_server.py
  --host "$HOST" --port "$PORT"
  --cert "$CERT" --key "$KEY"
  --kyber-sk "$KYBER_SK"
)

is_running() {
  [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

start() {
  if is_running; then
    echo "[i] already running: PID=$(cat "$PIDFILE")"
    exit 0
  fi

  # auto-generate cert/key if missing (self-signed SPKI)
  if [[ ! -f "$CERT" || ! -f "$KEY" ]]; then
    PUB="$HOME/.foritech/keys/kyber768_pub.bin"
    [[ -f "$PUB" ]] || { echo "[!] missing $PUB"; exit 2; }
    echo "[*] generating self-signed SPKI cert/key…"
    "$PY" -m foritech.cli.main x509-make --cn tls-demo --format spki \
      --pqc-pub "$PUB" --cert-out "$CERT" --key-out "$KEY"
  fi

  # warn if port already taken
  ss -ltnp 2>/dev/null | grep -q ":$PORT" && \
    echo "[!] port $PORT looks busy; continuing…"

  nohup "${cmd[@]}" >"$LOG" 2>&1 & echo $! > "$PIDFILE"
  sleep 0.5

  # TCP probe — аргументът $PORT е ПРЕДИ heredoc-а
  if python - "$PORT" <<'PY' 2>/dev/null
import socket,sys
s=socket.socket(); s.settimeout(0.5)
try:
  port=int(sys.argv[1]) if len(sys.argv)>1 else 8443
  s.connect(("127.0.0.1", port))
  print("OK")
except Exception:
  sys.exit(1)
finally:
  s.close()
PY
  then
    echo "[OK] started PID=$(cat "$PIDFILE")  log=$LOG"
  else
    echo "[!] failed to start, see $LOG"
    exit 1
  fi
}

stop() {
  if ! is_running; then
    echo "[i] not running"
    rm -f "$PIDFILE"
    exit 0
  fi
  kill "$(cat "$PIDFILE")" || true
  sleep 0.2
  is_running && kill -9 "$(cat "$PIDFILE")" || true
  rm -f "$PIDFILE"
  echo "[OK] stopped"
}

status() {
  if is_running; then
    echo "[OK] running PID=$(cat "$PIDFILE")"
    ss -ltnp 2>/dev/null | grep ":$PORT" || true
  else
    echo "[i] not running"
  fi
}

logs()   { exec tail -n 100 -f "$LOG"; }
health() { curl -ks "https://127.0.0.1:$PORT/healthz" || true; }

case "${1:-}" in
  start)   start ;;
  stop)    stop ;;
  restart) stop; start ;;
  status)  status ;;
  logs)    logs ;;
  health)  health ;;
  *) echo "Usage: $0 {start|stop|restart|status|logs|health}"; exit 2 ;;
esac
