# Release notes

## v0.5.0

**Core**
- Streaming wrap/unwrap + CLI auto/forced stream; META показва `STREAM/CHUNK`.
- SEC-1..3: header-MAC, strict режим, проверка ред на фреймове, tamper detect.

**X.509**
- Hybrid ext (raw / SPKI-b64), `x509-info`, `x509-extract-pqc`, `x509-make[-ca]`, `x509-issue`, `x509-verify`.

**Keys**
- `keygen`, `key-list`, `key-show`.

**TLS-PQC**
- Sessions + ротация (demo client/server).

**Tests**
- 13 passed, 1 skipped (локално при dev setup).

**Notes**
- Добавени скриптове за локална хигиена/сканиране: `scripts/scan_secrets.sh`, `scripts/setup_git_exclude.sh`.

## v0.5.1 — tidy & docs
- Code tidy (ruff), no functional changes
- Investor demo TLS quickstart
- CA bundles and verification docs
- Clean venv, deterministic tests
