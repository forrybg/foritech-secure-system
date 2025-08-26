import pytest
from pathlib import Path
from foritech.pki.x509_tools import generate_hybrid_selfsigned, extract_hybrid_info

@pytest.mark.skip(reason="x509 hybrid: pending TLS integration & SPKI format")
def test_x509_hybrid_extension_roundtrip(tmp_path: Path):
    pub = Path.home()/".foritech/keys/kyber768_pub.bin"
    if not pub.exists():
        pytest.skip("Missing Kyber public key", allow_module_level=True)
    cert_pem, key_pem = generate_hybrid_selfsigned("foritech-demo","Kyber768", pub.read_bytes())
    info = extract_hybrid_info(cert_pem)
    assert info and info["kem"]=="Kyber768"
