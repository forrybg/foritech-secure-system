 # Foritech Secure System – Roadmap

This project integrates **post-quantum cryptography (PQC)** (via [liboqs](https://github.com/open-quantum-safe/liboqs)) into a Python SDK and CLI for secure key management and data protection.

---

## ✅ Current Status
- Kyber768 KEM support (via liboqs-python bindings).
- Working  API for Data Encryption Keys (DEKs).
- CLI tools: , , .
- Tests passing (API, CLI, examples).
- GitHub CI workflows ( and  builds).

---

## 🔜 Next Milestones

### 1. SDK / API
- [ ] Finalize stable API surface ().
- [ ] Improve error handling ( classes).
- [ ] Add type hints + Pydantic models.
- [ ] Expand test coverage.

### 2. CLI / Examples
- [ ] Extend CLI with file backup/restore flows.
- [ ] Add  /  subcommands.
- [ ] Provide clear usage documentation.

### 3. X.509 / Hybrid Certificates
- [ ] Integrate PQC KEMs into X.509 certificate generation.
- [ ] Provide hybrid certificates (RSA/ECDSA + Kyber).
- [ ] Demo TLS handshake with OpenSSL + PQC certs.

### 4. DevOps / Distribution
- [ ] Docker image (SDK + liboqs prebuilt).
- [ ] PyPI distribution ( lite).
- [ ] Expand CI matrix (Python 3.10–3.13, Ubuntu, macOS, Windows).

### 5. Use Cases & Demos
- [ ] Secure file backup system with PQC protection.
- [ ] MinIO/S3 integration for cloud backups.
- [ ] REST API demo service using PQC for key exchange.

---

## 🌍 Funding & EU Programs
This project aligns with EU strategic priorities in **digital resilience** and **cybersecurity**.  
Potential funding frameworks include:
- **Horizon Europe** (Cluster 3 – Civil Security for Society).  
- **Digital Europe Programme** (advanced digital skills, cybersecurity).  
- **CEF Digital** (Cross-border digital infrastructures).  

We plan to propose **hybrid X.509 certificates** and **secure backup services** as real-world use cases, suitable for pilot adoption and EU funding.

---

## 🚀 Long-Term Vision
- Production-ready PQC SDK for developers.  
- Hybrid TLS toolkit for enterprises.  
- Collaboration with industry and academia.  
- Funding & expansion via EU digital security programs.  

