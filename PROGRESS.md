# Foritech Secure System — Progress Log

## 2025-08-26
- feat(cli): auto-stream for files >=64MiB; --stream/--no-stream and threshold flag
- chore(progress): auto-update PROGRESS.md
- feat(stream): add chunked AEAD streaming core and API wiring
- chore(gitignore): ignore only root /src; allow sdk/src
- feat(stream): chunked AEAD streaming (Kyber768 + ChaCha20-Poly1305); add stress script
- chore(progress): auto-update PROGRESS.md
- dev: pin local Python 3.12 via .python-version
- chore(progress): auto-update PROGRESS.md
- ci: pin Python 3.12; add foritech --help; archive noisy workflows
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity

## 2025-08-26
- feat(stream): add chunked AEAD streaming core and API wiring
- chore(gitignore): ignore only root /src; allow sdk/src
- feat(stream): chunked AEAD streaming (Kyber768 + ChaCha20-Poly1305); add stress script
- chore(progress): auto-update PROGRESS.md
- dev: pin local Python 3.12 via .python-version
- chore(progress): auto-update PROGRESS.md
- ci: pin Python 3.12; add foritech --help; archive noisy workflows
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- chore(progress): auto-update PROGRESS.md
- ci: make foritech CLI smoke test friendly; pin everything to py3.12

## 2025-08-26
- dev: pin local Python 3.12 via .python-version
- chore(progress): auto-update PROGRESS.md
- ci: pin Python 3.12; add foritech --help; archive noisy workflows
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- chore(progress): auto-update PROGRESS.md
- ci: make foritech CLI smoke test friendly; pin everything to py3.12
- chore(progress): auto-update PROGRESS.md
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- test: drop legacy tests expecting old API; keep minimal Kyber roundtrip/meta
- chore(progress): nightly snapshot

## 2025-08-26
- ci: pin Python 3.12; add foritech --help; archive noisy workflows
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- chore(progress): auto-update PROGRESS.md
- ci: make foritech CLI smoke test friendly; pin everything to py3.12
- chore(progress): auto-update PROGRESS.md
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- test: drop legacy tests expecting old API; keep minimal Kyber roundtrip/meta
- chore(progress): nightly snapshot
- chore(progress): auto-update PROGRESS.md
- chore: ignore embedded repos and local artifacts

## 2025-08-26
- ci: make foritech CLI smoke test friendly; pin everything to py3.12
- chore(progress): auto-update PROGRESS.md
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- test: drop legacy tests expecting old API; keep minimal Kyber roundtrip/meta
- chore(progress): nightly snapshot
- chore(progress): auto-update PROGRESS.md
- chore: ignore embedded repos and local artifacts
- chore(progress): auto-update PROGRESS.md
- chore: remove external tests & embedded repo; keep minimal Foritech tests; tidy .gitignore
- chore: sanitize repo layout (single sdk/src/foritech, tests/ at root, cleanup)

## 2025-08-26
- ci: archive old workflows; add CI • 3.12 and CI • Lite; nightly curiosity
- test: drop legacy tests expecting old API; keep minimal Kyber roundtrip/meta
- chore(progress): nightly snapshot
- chore(progress): auto-update PROGRESS.md
- chore: ignore embedded repos and local artifacts
- chore(progress): auto-update PROGRESS.md
- chore: remove external tests & embedded repo; keep minimal Foritech tests; tidy .gitignore
- chore: sanitize repo layout (single sdk/src/foritech, tests/ at root, cleanup)
- chore: add dev-check and dev-demo scripts
- chore: stabilize src layout, CLI, editable install; add crypto placeholders

## 2025-08-26
- chore(progress): auto-update PROGRESS.md
- chore: ignore embedded repos and local artifacts
- chore(progress): auto-update PROGRESS.md
- chore: remove external tests & embedded repo; keep minimal Foritech tests; tidy .gitignore
- chore: sanitize repo layout (single sdk/src/foritech, tests/ at root, cleanup)
- chore: add dev-check and dev-demo scripts
- chore: stabilize src layout, CLI, editable install; add crypto placeholders
- chore: add core mover script
- api: add generate_kem_keypair/save_secret/save_pubjson/recipients_from_files; cli: minimal kem-genkey main()
- cli: robust __main__ launcher for -m execution; api: add save_pubjson(pub_b64/kid)

## 2025-08-26
- chore: ignore embedded repos and local artifacts
- chore(progress): auto-update PROGRESS.md
- chore: remove external tests & embedded repo; keep minimal Foritech tests; tidy .gitignore
- chore: sanitize repo layout (single sdk/src/foritech, tests/ at root, cleanup)
- chore: add dev-check and dev-demo scripts
- chore: stabilize src layout, CLI, editable install; add crypto placeholders
- chore: add core mover script
- api: add generate_kem_keypair/save_secret/save_pubjson/recipients_from_files; cli: minimal kem-genkey main()
- cli: robust __main__ launcher for -m execution; api: add save_pubjson(pub_b64/kid)
- cli: make foritech.cli runnable (-m) with package __main__; api: add save_secret(0600)

## 2025-08-26
- chore: remove external tests & embedded repo; keep minimal Foritech tests; tidy .gitignore
- chore: sanitize repo layout (single sdk/src/foritech, tests/ at root, cleanup)
- chore: add dev-check and dev-demo scripts
- chore: stabilize src layout, CLI, editable install; add crypto placeholders
- chore: add core mover script
- api: add generate_kem_keypair/save_secret/save_pubjson/recipients_from_files; cli: minimal kem-genkey main()
- cli: robust __main__ launcher for -m execution; api: add save_pubjson(pub_b64/kid)
- cli: make foritech.cli runnable (-m) with package __main__; api: add save_secret(0600)
- pqc_kem: add ML-KEM→Kyber normalization; api: add generate_kem_keypair(); cli: normalize alg arg
- crypto(pqc_kem): pin to liboqs-python KeyEncapsulation API; export helpers; fix CLI imports

## 2025-08-25
- ✅ Step 1: PQC ядро (Kyber768 wrap/unwrap) стабилизирано
- ✅ Test roundtrip: OK
- ✅ CLI поправено
- ✅ CI workflows активни
- ⏸ x509 hybrid certs — pending (Step 1 leftover)

## 2025-08-26
- 🚧 Step 2: SDK / API polishing
  - Typed API (Pydantic/dataclasses)
  - Custom ForitechError слой
  - CLI usage docs
  - Packaging (PyPI lite + Docker image)
