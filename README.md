# Foritech

Скелет за стабилен SDK/API и CLI.

## CI
![CI • 3.12](https://github.com/forrybg/foritech-secure-system/actions/workflows/ci.yml/badge.svg)
![CI • Lite](https://github.com/forrybg/foritech-secure-system/actions/workflows/ci-lite.yml/badge.svg)

## Hybrid X.509 (CA / Issue / Info)

Foritech може да „вгражда“ PQC (Kyber) публичен ключ в custom X.509 extension (частен OID). Това е MVP за бъдещ хибриден TLS.

### Предпоставки
- Генериран Kyber ключ:
  ```bash
  python scripts/kyber-keygen.py
  # ще създаде: ~/.foritech/keys/kyber768_pub.bin и kyber768_sec.bin

pip install -e . && foritech --help
1) Self-signed CA
foritech x509-make-ca --cn "foritech-ca" \
  --cert-out ca_cert.pem --key-out ca_key.pem

2) Издай leaf сертификат (вграден Kyber pub)
foritech x509-issue --cn "foritech-leaf" --kem Kyber768 \
  --pqc-pub "$HOME/.foritech/keys/kyber768_pub.bin" \
  --ca-cert ca_cert.pem --ca-key ca_key.pem \
  --cert-out leaf_cert.pem

3) Преглед на extension-а
foritech x509-info --in leaf_cert.pem
# X509: kem=Kyber768 format=raw pqc_pub_b64_len=... v=1

foritech x509-info --in leaf_cert.pem
# X509: kem=Kyber768 format=raw pqc_pub_b64_len=... v=1

По желание с OpenSSL (OID ще е „непознат“, което е очаквано):
openssl x509 -in leaf_cert.pem -noout -text | awk '/X509v3 extensions/{flag=1} flag'

Бележки

Грешките в PKI слоя се мапват към ForitechError (по-ясни runtime съобщения).

Extension payload е JSON (MVP): {kem, pqc_pub_b64, format:"raw", v:1}. По-нататък ще добавим format:"spki-b64".
Backup Policy (силно препоръчително)

Винаги прави snapshot преди сериозни промени:
scripts/backup_snapshot.sh

И локален бекъп на ключови файлове преди редакция:
scripts/backup_file.sh sdk/src/foritech/pki/x509_tools.py
scripts/backup_file.sh sdk/src/foritech/cli/main.py


---

# TLS-PQC Sessions (Kyber768) — Demo

В репото има минимален клиент/сървър протокол за сесии върху HTTPS:
- KEM: **Kyber768** (чрез `liboqs-python`)
- Payload AEAD: **ChaCha20-Poly1305**
- Ротация на ключа: HKDF(KEK, "foritech-keyupdate|epoch=\<n\>")

## Бърз старт

1) Инсталация (editable):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

Генерирай Kyber ключове (ако още нямаш):
python scripts/kyber-keygen.py
# запомни:
#   Публичен: $HOME/.foritech/keys/kyber768_pub.bin
#   Таен    : $HOME/.foritech/keys/kyber768_sec.bin
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"

Хибриден X.509 със SPKI PQC разширение:
foritech x509-make --cn spki-demo --format spki \
  --pqc-pub "$HOME/.foritech/keys/kyber768_pub.bin" \
  --cert-out spki_self.pem --key-out spki_self.key
foritech x509-info --in spki_self.pem

Стартирай сървъра (TLS, използва горния cert):
python scripts/tls_pqc_server.py --host 127.0.0.1 --port 8443 \
  --cert spki_self.pem --key spki_self.key

Клиент: handshake + сесия + ротация:
python scripts/tls_pqc_client.py --host 127.0.0.1 --port 8443
# ще видиш: session_id, batch изпращания, rotated=True при key update и OK ✅

⚠️ Сигурност/хигиена: Не комитвай *.pem / *.key. В .gitignore вече има правила.
Какво включва SDK-то до v0.4.0

foritech CLI:

wrap/unwrap (авто-stream за ≥64MiB; --stream/--no-stream)

meta (показва KID, KEM, STREAM/CHUNK)

X.509: x509-info, x509-make, x509-make-ca, x509-issue (raw/SPKI)

Python:

foritech.api (file/stream wrap/unwrap)

foritech.pki.x509_tools (хибридни разширения raw/spki)

foritech.tlspqc (TLS-PQC клиент със сесии)

Тестове
pytest -q
# цел: всички зелено; интеграционният TLS-PQC тест се skip-ва без Kyber ключове.


## Makefile бързи цели

```bash
make gen-keys             # генерира Kyber ключове и подсказва FORITECH_SK
make x509-self-spki       # self-signed X.509 с SPKI PQC extension
make run-server           # стартира TLS-PQC демо сървър (ползва $(CERT)/$(KEY))
make run-client           # клиент (handshake + demo обмен)
make ping                 # handshake + batch-и + ротация + bye (един изстрел)

make wrap-demo            # малък файл: wrap/unwrap
make stream-demo          # 128MiB файл: авто-stream wrap/unwrap

make test                 # pytest -q
make fmt && make lint     # ruff fix / check
make typecheck            # mypy
make clean                # чисти локални артефакти (*.pem/*.key/enc/out)


### CI: Demo • TLS-PQC smoke (manual)
Има ръчен workflow **Demo • TLS-PQC smoke** (Runs on: `self-hosted, linux`), който:
1) създава venv и инсталира SDK;
2) генерира Kyber ключове;
3) прави SPKI self-signed cert;
4) стартира demo сървър + пуска клиента;
5) качва `server.log` и `client.log` като артефакти.

> Ако `liboqs-python (oqs)` липсва на runner-а, job-ът се **скипва** (успешно), без да чупи таблото.


---
### Investor docs
See **Investor Docs Pack** → https://github.com/forrybg/foritech-investor-demo/tree/docs-pack
