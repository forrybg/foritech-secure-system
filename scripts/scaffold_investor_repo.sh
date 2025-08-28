#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")"/.. && pwd)"
TARGET="${1:-$HERE/../foritech-investor-demo}"

echo ">> Target: $TARGET"
if [[ -e "$TARGET" && ! -d "$TARGET" ]]; then
  echo "ERROR: $TARGET exists and is not a directory" >&2
  exit 2
fi

mkdir -p "$TARGET"/{scripts,certs}
cd "$TARGET"

# .gitignore (не качваме venv, cache и чувствителни certs/keys)
cat > .gitignore <<'GIT'
.venv/
__pycache__/
*.pyc
certs/
GIT

# README с инструкции
cat > README.md <<'MD'
# Foritech Investor Demo

Minimal demo to show:
- PQC TLS session (Kyber768) with our sample server/client
- File wrap/unwrap via the `foritech` CLI

## 0) Prepare venv

```bash
python3 -m venv .venv
source .venv/bin/activate
# Install the SDK from the sibling repo:
pip install -e ../foritech-secure-system

If you want Kyber (TLS-PQC) support, also ensure liboqs and oqs python are installed as per the main repo’s scripts/dev_install_oqs.sh.
1) Bring certs/keys

Copy a fullchain + server key here (or point the run script to your files):
cp ../foritech-secure-system/pki/issued/leaf-sub1_fullchain.pem certs/server_cert.pem
cp ../foritech-secure-system/pki/issued/leaf-sub1.key         certs/server_key.pem

Export Kyber secret (if different, adjust path):
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"

2) Run

Terminal A:
scripts/run_server.sh

Terminal B:
scripts/run_client.sh

You should see the KEM info and a pong:... reply.
3) File wrap/unwrap smoke
echo "hi" > s.txt
foritech wrap --in s.txt --out s.enc --recipient raw:$HOME/.foritech/keys/kyber768_pub.bin --kid demo
foritech unwrap --in s.enc --out s.out
diff -u s.txt s.out && echo "OK ✅"

This demo repo intentionally ignores certs/ in git. Do not commit secrets.
MD
Копие на TLS-PQC server/client от основното repo (за да е самодостатъчно)

cp "$HERE/scripts/tls_pqc_server.py" scripts/tls_pqc_server.py
cp "$HERE/scripts/tls_pqc_client.py" scripts/tls_pqc_client.py

Run-скриптове, удобни за инвеститорската демо среда

cat > scripts/run_server.sh <<'SRV'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CERT="${1:-certs/server_cert.pem}"
KEY="${2:-certs/server_key.pem}"
KYBER_SK="${KYBER_SK:-${FORITECH_SK:-$HOME/.foritech/keys/kyber768_sec.bin}}"

if [[ ! -f "$CERT" || ! -f "$KEY" ]]; then
echo "Missing cert/key in ./certs (or pass paths):" >&2
echo " scripts/run_server.sh [cert] [key]" >&2
exit 2
fi

exec python3 scripts/tls_pqc_server.py
--host 0.0.0.0 --port 8443
--cert "$CERT"
--key "$KEY"
--kyber-sk "$KYBER_SK"
SRV
chmod +x scripts/run_server.sh

cat > scripts/run_client.sh <<'CLI'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${1:-127.0.0.1}"
PORT="${2:-8443}"
exec python3 scripts/tls_pqc_client.py --host "$HOST" --port "$PORT"
CLI
chmod +x scripts/run_client.sh

echo
echo "== Investor demo scaffolded =="
echo "Location: $TARGET"
echo "Next steps:"
echo " 1) cd "$TARGET""
echo " 2) python3 -m venv .venv && source .venv/bin/activate"
echo " 3) pip install -e ../foritech-secure-system"
echo " 4) cp ../foritech-secure-system/pki/issued/leaf-sub1_fullchain.pem certs/server_cert.pem"
echo " cp ../foritech-secure-system/pki/issued/leaf-sub1.key certs/server_key.pem"
echo " 5) export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin""
echo " 6) scripts/run_server.sh # in terminal A"
echo " scripts/run_client.sh # in terminal B"
