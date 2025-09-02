# Security Policy

This repository contains production-grade code for the FORITECH Secure System.
We take the security of our users and partners seriously and welcome responsible reports.

## Reporting a Vulnerability

- **Private only**: Do not open public issues for security topics.
- Prefer **GitHub Security Advisories** (recommended).
- Backup contact: **security@foritech.example** (temporary: **forrybg.hh@gmail.com**).
- Include: impact, affected version/commit, clear reproduction steps, and a minimal PoC.
- Please avoid data exfiltration. Use test data/keys only.

PGP: *TBD (public key to be published)*

## Service Level Objectives

- **Acknowledgement**: within **72 hours** (business days).
- **Triage & severity**: within **5 days** (CVSS v3.x).
- **Fix/mitigation target**:
  - **Critical/High**: ≤ **30 days**
  - **Medium**: ≤ **60 days**
  - **Low/Info**: best effort
- We will coordinate disclosure and publish advisories. CVEs will be requested when eligible.

## Supported Versions

| Branch / Line | Status              | Notes                          |
|---------------|---------------------|--------------------------------|
| `main`        | **Supported**       | Active development             |
| `0.5.x`       | **Supported**       | Latest minor tag in 0.5 series |
| older lines   | **End-of-life**     | No regular fixes               |

Security fixes are backported to the latest supported minor line where feasible.

## In Scope (examples)

- Remote code execution, sandbox escapes
- AuthN/AuthZ bypass, privilege escalation, session fixation
- Crypto weaknesses in our usage (OpenSSL/OQS): confidentiality/integrity breaks
- Supply-chain risks impacting this repo (malicious deps, tampered artifacts)
- Secret leakage in this repo or build artifacts (tokens, private keys)
- TLS/X.509 handling defects (verification, chain building, hybrid PQC modes)

## Out of Scope (examples)

- Denial of Service via resource exhaustion or rate limits
- Vulnerabilities in third-party services not controlled by us
- Social engineering, physical attacks, lost/stolen devices
- Low-impact information disclosures in **demo-only** assets
- Issues that require privileged/local system access beyond our threat model

If in doubt, report privately — we will confirm scope.

## Research Rules & Safe Harbor

- Do not harm users or data; do not exfiltrate real data.
- No privacy violations, service disruption, or lateral movement.
- Use your own accounts/test data and **test keys** only.
- We will not pursue legal action for research performed in good faith, within this policy.

## Secrets & Key Material

- Never commit real secrets/keys/certs. Use provided **demo/test** material only.
- If you find a secret in history or artifacts, **report privately immediately**.
- We will revoke, rotate, and publish remediation guidance.

## Cryptography Policy

- We do **not** implement custom primitives. We rely on vetted libraries (OpenSSL, OQS provider).
- Post-quantum algorithms (e.g., ML-KEM/Kyber, Dilithium) are used per upstream guidance.
- Configuration hardening (TLS, X.509, hybrid) follows current best practices and may evolve.

## Disclosure

We follow coordinated disclosure. We acknowledge reporters (opt-in) after fixes are available.
Thank you for helping us keep the ecosystem safe.
