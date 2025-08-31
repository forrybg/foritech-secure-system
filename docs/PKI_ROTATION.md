# PKI: CRL/OCSP и ротация (кратко)

## CRL
- Поддържаме Sub-CA CRL през OpenSSL CA DB (`pki/subca/ca-db`).
- Инициализация: `scripts/pki_init_db.sh`
- Публикуване на CRL: `scripts/pki_crl_gen.sh` → `pki/bundles/issuing.crl.pem`
- Ревокация: `scripts/pki_revoke.sh --cert <leaf.pem>` (авто-генерира нов CRL)

## OCSP (по избор за демо)
- Издаваме OCSP signer: `scripts/ocsp_issue_signer.sh`
- Стартираме responder: `scripts/ocsp_run.sh 2560`
- Проверка: `scripts/ocsp_check.sh pki/issued/leaf-sub1.pem`

## Ротация
- **Leaf**: на 60–90 дни. `scripts/ca_rotate_leaf.sh <CN> [PQC_PUB]` → обновява `pki/bundles/`.
- **Sub-CA**: annually, с припокриване:
  1) `scripts/ca_rotate_subca.sh "Foritech Issuing CA 2"`
  2) Преиздай активните leaf-ове към новата Sub-CA (поетапно).
  3) Публикувай CRL на старата Sub-CA след миграцията.

## Публикуване
- От “сървърите”: bundle `pki/bundles/fullchain.pem` (+ при нужда CRL `issuing.crl.pem`).
- Клиенти, които валидират CRL: конфигурирай `CRL` URL или кеш.

## Бележки
- Root офлайн.
- Sub-CA онлайн (с защитен ключ) или в HSM; backup на ключовете е задължителен.
- Логване и мониторинг на CRL timestamp/OCSP status.
