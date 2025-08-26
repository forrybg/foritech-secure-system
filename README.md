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

