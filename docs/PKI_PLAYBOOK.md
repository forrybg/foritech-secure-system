# Foritech PKI Playbook (Root → Leaf)

Цел: практично, без breaking changes, върху наличните CLI команди.

## Директории (локално)
- `pki/root/`  – офлайн Root CA: `root.pem` (публичен), `root.key` (секретен).
- `pki/issued/` – издадени leaf-ове: `<CN>.pem`, `<CN>_fullchain.pem`.

> Скриптът `scripts/setup_git_exclude.sh` вече игнорира `*.pem/*.key/*.chain`.

## 1) Root CA (офлайн)
```bash
bash scripts/ca_make_root.sh
# Параметри (по желание):
#   CN="Foritech Root CA 2025" DAYS=3650 OUT_DIR=pki/root FORCE=1 bash scripts/ca_make_root.sh

Нужен е PQC публичен ключ:
foritech keygen --kid demo-k1
# ще създаде ~/.foritech/keys/demo-k1_pub.bin

Издаване:
# по подразбиране FORMAT=spki, DAYS=825
CN=leaf-01 PQC_PUB="$HOME/.foritech/keys/demo-k1_pub.bin" bash scripts/ca_issue_leaf.sh

Резултат:

pki/issued/leaf-01.pem (leaf)

pki/issued/leaf-01_fullchain.pem (leaf + root)
Верификация
bash scripts/x509_verify_chain.sh pki/issued/leaf-01.pem pki/issued/leaf-01_fullchain.pem pki/root/root.pem
# Очаквано: CHAIN OK ...

Оперативни бележки

Пазете root.key офлайн (правете издаването на защитена машина).

Дистрибутирайте само leaf.pem/*_fullchain.pem към услуги/клиенти.

Ротация: нов leaf преди изтичане; нов Root по план (напр. на 10 години).

(Следваща фаза) Sub-CA/Issuing CA + OCSP/CRL.
