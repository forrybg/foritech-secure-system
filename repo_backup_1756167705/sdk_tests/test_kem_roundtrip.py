import pytest

try:
    OQS_AVAILABLE = True
except Exception:
    OQS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not OQS_AVAILABLE, reason="liboqs-python not installed")

ALGOS = ["ml-kem-512", "ml-kem-768", "ml-kem-1024"]

@pytest.mark.parametrize("alg", ALGOS)
def test_kem_roundtrip(alg):
    from foritech.crypto.pqc_kem import kem_generate, kem_encapsulate, kem_decapsulate
    pub, sec = kem_generate(alg)
    ct, shared1 = kem_encapsulate(pub, alg)
    shared2 = kem_decapsulate(ct, sec, alg)
    assert isinstance(shared1, (bytes, bytearray))
    assert shared1 == shared2
    assert len(shared1) >= 16
