# ForiTech Secure System SDK

PQC-ready PKI toolkit (combiners, hybrid X.509, ACME, CT privacy).

## License
This project is licensed under the Apache License 2.0 – see the [LICENSE](LICENSE) file for details.

### Attribution
- Uses cryptography (Apache/BSD)
- Uses Typer (MIT)
- Uses Rich (MIT)
- Will integrate liboqs (MIT)

## Tests & Coverage (local)

### 1) Setup (във venv)
```bash
cd sdk
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
python -m pip install pytest pytest-cov
