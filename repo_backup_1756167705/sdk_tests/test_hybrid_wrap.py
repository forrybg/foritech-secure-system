import pytest

try:
    OQS_AVAILABLE = True
except Exception:
    OQS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not OQS_AVAILABLE, reason="liboqs-python not installed")

class DummySigner:
    alg = "ml-dsa-44"
    def sign(self, data: bytes) -> bytes:
        import hashlib
        return hashlib.sha256(b"dummy" + data).digest()

def _mk_pub_json(pub_b: bytes, kid: str):
    from foritech.crypto.pqc_kem import b64e
    return {"kid": kid, "pub_b64": b64e(pub_b)}

def _decap_shared(ct_b64: str, sec: bytes, kem_alg: str):
    from foritech.crypto.pqc_kem import b64d, kem_decapsulate
    return kem_decapsulate(b64d(ct_b64), sec, kem_alg)

@pytest.mark.parametrize("kem_alg", ["ml-kem-768"])
def test_hybrid_wrap_multi_recipient(kem_alg):
    from foritech.crypto.pqc_kem import kem_generate
    from foritech.crypto.hybrid_wrap import hybrid_wrap_dek, hkdf

    pub1, sec1 = kem_generate(kem_alg)
    pub2, sec2 = kem_generate(kem_alg)

    recipients = [
        _mk_pub_json(pub1, "ops-1"),
        _mk_pub_json(pub2, "dr-1"),
    ]

    bundle = hybrid_wrap_dek(recipients, kem_alg=kem_alg, aad_str="backup:demo", signer=DummySigner())
    assert bundle["kem_alg"] == kem_alg
    assert bundle["cipher"] == "AES-256-GCM"
    assert bundle["sig_alg"] == "ml-dsa-44"
    assert "signature_b64" in bundle
    assert len(bundle["recipients"]) == 2

    # И двамата получатели могат да извлекат DEK (чрез HKDF(shared) -> KEKᵢ)
    from Crypto.Cipher import AES
    from foritech.crypto.pqc_kem import b64d
    for r, sec in zip(bundle["recipients"], [sec1, sec2]):
        shared = _decap_shared(r["kem_ciphertext_b64"], sec, kem_alg)
        info = b"foritech-mlkem-wrap" + b"backup:demo"
        kek = hkdf(salt=b"", ikm=shared, info=info, length=32)

        nonce = b64d(r["nonce_b64"])
        tag = b64d(r["tag_b64"])
        enc_dek = b64d(r["enc_dek_b64"])

        c = AES.new(kek, AES.MODE_GCM, nonce=nonce)
        c.update(b"backup:demo")
        dek = c.decrypt_and_verify(enc_dek, tag)

        assert isinstance(dek, (bytes, bytearray))
        assert len(dek) == 32
