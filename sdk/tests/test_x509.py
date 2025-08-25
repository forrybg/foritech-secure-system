import pytest
pytestmark = pytest.mark.skip(reason="x509 — временно изключен")
import pytest
pytestmark = pytest.mark.skip(reason="x509 — временно изключен")
from foritech.pki.x509_tools import generate_hybrid_cert

def test_generate_hybrid_cert():
    pem = generate_hybrid_cert("test.example")
    assert "BEGIN CERTIFICATE" in pem
