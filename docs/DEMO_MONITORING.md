# Foritech Demo – Monitoring & Health

Мини сетъп:
- Health endpoint: `GET /healthz` → `OK`
- Еднократен health probe → Prometheus textfile gauge: `/tmp/foritech-exporter/metrics.prom` (`pqc_up 0/1`)
- systemd timer на всяка минута
- Windows бърза проверка (PowerShell)

## Файлове
- `scripts/monitor_health.sh`
- `scripts/systemd/foritech-pqc-monitor.service`
- `scripts/systemd/foritech-pqc-monitor.timer`

## Предпоставки (server)
```bash
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"
scripts/server_bg.sh status
scripts/server_bg.sh health    # очакваш: OK

Еднократен probe
scripts/monitor_health.sh                     # HOST=127.0.0.1 PORT=8443 по подразбиране
HOST=192.168.5.9 PORT=8443 scripts/monitor_health.sh

Изход:

лог: logs/monitor.log

метрики: /tmp/foritech-exporter/metrics.prom
# HELP pqc_up 1 when demo is healthy, 0 otherwise
# TYPE pqc_up gauge
pqc_up 1

# HELP pqc_up 1 when demo is healthy, 0 otherwise
# TYPE pqc_up gauge
pqc_up 1

sudo cp scripts/systemd/foritech-pqc-monitor.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now foritech-pqc-monitor.timer

Проверка:
systemctl status foritech-pqc-monitor.timer
journalctl -u foritech-pqc-monitor.service -f
cat /tmp/foritech-exporter/metrics.prom
tail -n 50 logs/monitor.log

systemctl status foritech-pqc-monitor.timer
journalctl -u foritech-pqc-monitor.service -f
cat /tmp/foritech-exporter/metrics.prom
tail -n 50 logs/monitor.log

Windows бърза проверка (PowerShell)
$AllProtocols = [System.Net.SecurityProtocolType]'Tls12,Tls13'
[System.Net.ServicePointManager]::SecurityProtocol = $AllProtocols
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
try { (Invoke-WebRequest https://192.168.5.9:8443/healthz).Content }
finally { [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null }

Troubleshooting
Порт 8443 е зает: ss -ltnp | grep :8443, после scripts/server_bg.sh restart

“Server cert has no FORITECH hybrid extension”: на 8443 върви друг TLS, спри го и стартирай нашия

Файъруол: sudo ufw allow 8443/tcp (ако UFW е включен)
Uninstall
sudo systemctl disable --now foritech-pqc-monitor.timer
sudo rm -f /etc/systemd/system/foritech-pqc-monitor.{service,timer}
sudo systemctl daemon-reload

