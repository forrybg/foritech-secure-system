server/demo/Windows
Роли / Терминали

[SERVER] = ~/foritech-secure-system (стартираме TLS+Kyber сървъра)

[DEMO] = ~/foritech-investor-demo (пускаме клиента/диагностики)

0) Пререквизити
# ключове (ако още нямаш)
foritech keygen --kid demo-k1     # генерира Kyber768 двойка
# активирай чистата среда за сървъра (с oqs)
cd ~/foritech-secure-system
source .venv-clean/bin/activate

1) Стартиране на сървъра
Вариант A: foreground (видим лог в терминала)
# [SERVER]
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"
test -f pki/issued/tls-demo_fullchain.pem -a -f pki/issued/tls-demo.key || \
  foritech x509-make --cn tls-demo --format spki \
    --pqc-pub "$HOME/.foritech/keys/kyber768_pub.bin" \
    --cert-out pki/issued/tls-demo_fullchain.pem \
    --key-out  pki/issued/tls-demo.key

python scripts/tls_pqc_server.py --host 0.0.0.0 --port 8443 \
  --cert pki/issued/tls-demo_fullchain.pem \
  --key  pki/issued/tls-demo.key \
  --kyber-sk "$FORITECH_SK"

Вариант B: бекграунд helper (PID файл + лог)
# [SERVER]
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"
scripts/server_bg.sh start
scripts/server_bg.sh health     # очакваш: OK
scripts/server_bg.sh status
# лог:
scripts/server_bg.sh logs
# спиране/рестарт:
scripts/server_bg.sh stop
scripts/server_bg.sh restart

Вариант C: systemd unit (постоянен)
# [SERVER]
sudo cp scripts/systemd/foritech-pqc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now foritech-pqc.service
systemctl status foritech-pqc.service -n 20 --no-pager

2) Health, порт, логове
# [SERVER]
curl -k https://127.0.0.1:8443/healthz     # OK
ss -ltnp | grep :8443                       # слуша ли портът
tail -n 50 logs/pqc-server.log

3) Клиент (демо)
Локално към същия сървър
# [DEMO]
cd ~/foritech-investor-demo
. ../foritech-secure-system/.venv-clean/bin/activate
../foritech-secure-system/.venv-clean/bin/python \
  ../foritech-secure-system/scripts/tls_pqc_client.py \
  --host 127.0.0.1 --port 8443

От Windows (PowerShell) през SSH към Linux
# увери се, че ключът е зареден
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519

ssh -p 8022 -i $env:USERPROFILE\.ssh\id_ed25519 forybg@192.168.5.9 `
  'cd ~/foritech-investor-demo; . ../foritech-secure-system/.venv-clean/bin/activate; \
    ../foritech-secure-system/.venv-clean/bin/python \
    ../foritech-secure-system/scripts/tls_pqc_client.py --host 127.0.0.1 --port 8443'

4) Мониторинг (експортер + таймер + табло)
# еднократно:
# [SERVER]
scripts/monitor_health.sh
cat /tmp/foritech-exporter/metrics.prom

sudo cp scripts/systemd/foritech-pqc-monitor.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now foritech-pqc-monitor.timer
systemctl status foritech-pqc-monitor.timer
# табло (tmux):
tmux new -s pqcmon -d 'bash -lc "cd ~/foritech-secure-system && scripts/monitor_dashboard.sh"'

5) Бързи рестарти (Lite / Full)
# [SERVER]
bash scripts/foritechRestartStartlimitLite.sh   # чисти StartLimit и restart на unit-а
bash scripts/foritechRestartFull.sh             # kill порт, enable --now, health, tail

6) Често срещани съобщения

“Server cert has no FORITECH hybrid extension”
На порт 8443 се е вдигнал сървър с „гол“ (non-hybrid) X.509.
Решение: scripts/server_bg.sh stop && sudo systemctl stop foritech-pqc.service
После стартирай пак нашия (Вариант B или C).

Permission denied (publickey) при SSH
Зареди ключа:
Start-Service ssh-agent; ssh-add $env:USERPROFILE\.ssh\id_ed25519
Добави id_ed25519.pub в ~/.ssh/authorized_keys на Linux.

schannel: missing close_notify в PowerShell
Безобидно. Ползвай:
curl.exe -k --http1.1 https://<ip>:8443/healthz

Start request repeated too quickly (systemd)
Пусни Lite рестарт: bash scripts/foritechRestartStartlimitLite.sh

Pytest не намира модула
Увери се, че си в .venv-clean и в root на проекта:
source .venv-clean/bin/activate && pytest -q

7) Бърз бекъп (по избор)
# [SERVER]
./scripts/backup_snapshot.sh
# криптиран tar.gz в /tmp:
./scripts/backup_seal_host.sh
