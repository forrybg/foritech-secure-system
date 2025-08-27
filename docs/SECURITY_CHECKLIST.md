# Security checklist (dev)

## Local hygiene
- Run `scripts/setup_git_exclude.sh` (еднократно на машина) – игнорира локални ключове/артефакти.
- Keep `.venv/` and `third_party/` out of Git.

## Secret scanning
- Install: `pipx install trufflehog` (или `pip install trufflehog` в активния venv).
- Use: `scripts/scan_secrets.sh` (използва `--only-verified --fail`).

## Before tag/release
- `pytest -q` зелено.
- `foritech --help` – виждат се новите подкоманди.
- `foritech key-list` без неочаквани ключове, wrap/unwrap smoke ok.
- Ако има X.509 промени – `foritech x509-verify --leaf ... --chain ... [--root ...]`.

## Key/Cert ops
- Не комитвай `*.pem/*.key`. Генерирай локално и пази офлайн при нужда.
- За публични демота – използвай отделни демо-ключове.

## Roadmap (оперативно)
- Offline **Root CA** + Issuing CA, ротация/политики.
- OCSP/CRL (поетапно).
