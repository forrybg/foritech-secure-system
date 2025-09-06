# Work Plan (6 months)

**Project:** Foritech Secure System  
**Duration:** 6 months  
**Total budget:** EUR 49,800

## M1 (Months 1–2): Core PQC PKI + CI
**Deliverables**
- M1.D1 — CLI/SDK v0.6.0-rc1 (tag + changelog)
- M1.D2 — Tests (unit + e2e) incl. X.509 chain verify
- M1.D3 — GitHub Actions: lint, tests, progress-digest, CodeQL
- M1.D4 — Docs: quickstart, SECURITY.md, CONTRIBUTING.md

**Acceptance**
- All required CI jobs pass; ≥80% unit coverage for PKI module
- `make demo-pqc-ca` produces a verifying chain
- Two tags: baseline v0.5.x and v0.6.0-rc1

## M2 (Months 3–4): Hybrid TLS + Demos
**Deliverables**
- M2.D1 — Docker images + Makefile targets (OQS-OpenSSL)
- M2.D2 — Example cert profiles (root/subCA/leaf, hybrid)
- M2.D3 — Screencast + tutorial

**Acceptance**
- `docker compose up` server + functional client handshake (hybrid)
- Compatibility notes (KEM/cipher lists)
- Demo validated on GPU worker + dev machine

## M3 (Months 5–6): DID/SSI + ZK & Hardening
**Deliverables**
- M3.D1 — Minimal DID/SSI + ZK login demo
- M3.D2 — Threat model + security notes
- M3.D3 — v0.6.0 stable release (tags, assets)
- M3.D4 — Upstream report (opened issues/PRs)

**Acceptance**
- ZK login demo verified end-to-end
- Hardening checklist applicable in practice
- Public v0.6.0 with docs/assets

## KPIs
- 3 tagged releases (incl. final v0.6.0)
- ≥5 external issues/discussions; ≥2 external PRs reviewed/merged
- 1 screencast + 2 tutorials
