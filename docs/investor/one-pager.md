# Foritech Secure System — One-Pager

**Project:** Foritech Secure System (PQC PKI/TLS + DID/SSI + Zero-Knowledge auth)  
**Applicant:** Foritech (solo applicant), contact: <add email>  
**License:** Apache-2.0 (code), CC-BY 4.0 (docs)  
**Duration:** 6 months  
**Budget:** EUR 49,800 (cost-recovery)  
**Repo:** https://github.com/forrybg/foritech-secure-system

## Problem
Classical PKC (RSA/ECC) is vulnerable to quantum adversaries. Need a practical, open, vendor-neutral path to PQC-ready TLS & PKI.

## Solution
- PQC-ready X.509 chain tooling (Kyber/Dilithium, hybrid profiles)
- Hybrid TLS demos via OQS/OpenSSL
- DID/SSI + Zero-Knowledge auth (privacy-preserving)
- CLI + Python SDK, CI, tests, container images

## What’s new
- End-to-end PQC PKI with safe defaults and hybrid compatibility  
- Developer-first UX (one-command demos, CI recipes)  
- Privacy by design (minimal PII, optional ZK/DID)  
- Standards/upstream focus (NIST PQC, IETF, liboqs/OQS-OpenSSL)

## Beneficiaries
FOSS devs, SMEs, public bodies, research/education.

## Results (deliverables)
- D1: PQC PKI/CLI v0.6.0 (tag, docs, tests)
- D2: Hybrid TLS demo (Docker/Make)
- D3: Minimal DID/SSI + ZK login demo
- D4: Threat model & “13+2” hardening notes
- D5: Adoption kit: tutorials, one-click demo, screencast
- D6: Upstream report (issues/PRs)

## Openness & sustainability
Apache-2.0 (code), CC-BY 4.0 (docs). All artifacts public; continued maintenance & small bounties after grant.
