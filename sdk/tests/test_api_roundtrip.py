# sdk/tests/test_api_roundtrip.py
import os, json, pytest

import os

import os
import pytest
try:
    import oqs as _oqs
    _ENABLED_KEMS = set(getattr(_oqs, 'get_enabled_kems', lambda: [])())
except Exception:  # pragma: no cover
    _ENABLED_KEMS = set()
def _pick_kem_for_tests():
    env = os.environ.get('FORITECH_TEST_KEM')
    if env:
        return env
    if 'Kyber768' in _ENABLED_KEMS:
        return 'kyber768'
    return KEM_FOR_TESTS
KEM_FOR_TESTS = _pick_kem_for_tests()
try:
    import oqs as _oqs
    _ENABLED_KEMS = set(getattr(_oqs,'get_enabled_kems',lambda:[])())
except Exception:
    _ENABLED_KEMS = set()

try:
    import oqs  # noqa: F401
    OQS_AVAILABLE = True
except Exception:
    OQS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not OQS_AVAILABLE, reason="liboqs-python not installed")

def test_api_wrap_unwrap_roundtrip(tmp_path):
    from foritech.api import (
        generate_kem_keypair, save_secret, save_pubjson, recipients_from_files,
        wrap_existing_dek_for, unwrap_dek
    )
    from Crypto.Cipher import AES

    # 1) двама получателя
    pub1_b64, sec1 = generate_kem_keypair(KEM_FOR_TESTS)
    pub2_b64, sec2 = generate_kem_keypair(KEM_FOR_TESTS)

    a_pub = tmp_path / "ops-1.kem.pub.json"
    a_sec = tmp_path / "ops-1.kem.sec"
    b_pub = tmp_path / "dr-1.kem.pub.json"
    b_sec = tmp_path / "dr-1.kem.sec"

    save_pubjson(a_pub, pub1_b64, kid="ops-1")
    save_secret(a_sec, sec1)
    save_pubjson(b_pub, pub2_b64, kid="dr-1")
    save_secret(b_sec, sec2)

    recips = recipients_from_files([a_pub, b_pub])

    # 2) данни + AAD
    plain = b"hello pqc api"
    aad = "demo-aad"
    dek = os.urandom(32)  # 256-bit

    # 3) wrap на DEK към двамата
    bundle = wrap_existing_dek_for(dek, recips, aad=aad, alg=KEM_FOR_TESTS)
    assert bundle["cipher"] == "AES-256-GCM"
    assert bundle["kem_alg"] in (KEM_FOR_TESTS, "ML-KEM-768", "Kyber768")
    assert len(bundle["recipients"]) == 2

    # 4) шифрираме с DEK (локално)
    nonce = os.urandom(12)
    c = AES.new(dek, AES.MODE_GCM, nonce=nonce)
    c.update(aad.encode())
    enc, tag = c.encrypt_and_digest(plain)

    # 5) ops-1 възстановява DEK и дешифрира
    dek1 = unwrap_dek(bundle, kid="ops-1", sec_bytes=a_sec.read_bytes(), aad=aad, alg=KEM_FOR_TESTS)
    assert isinstance(dek1, (bytes, bytearray)) and len(dek1) == 32
    c2 = AES.new(dek1, AES.MODE_GCM, nonce=nonce)
    c2.update(aad.encode())
    got = c2.decrypt_and_verify(enc, tag)
    assert got == plain


def test_api_wrong_aad_fails(tmp_path):
    import os
    import pytest
    from foritech.api import (
        generate_kem_keypair, save_secret, save_pubjson, recipients_from_files,
        wrap_existing_dek_for, unwrap_dek
    )

    # генерираме ключ
    pub_b64, sec = generate_kem_keypair(KEM_FOR_TESTS)
    p_pub = tmp_path/"u1.kem.pub.json"; p_sec = tmp_path/"u1.kem.sec"
    save_pubjson(p_pub, pub_b64, kid="u1"); save_secret(p_sec, sec)

    # recipient set
    recips = recipients_from_files([p_pub])

    # wrap с "good" AAD
    dek = os.urandom(32)
    bundle = wrap_existing_dek_for(dek, recips, aad="good", alg=KEM_FOR_TESTS)

    # опит за unwrap с лош AAD → очакван ValueError от вътрешното AES-GCM
    with pytest.raises(ValueError):
        unwrap_dek(bundle, kid="u1", sec_bytes=p_sec.read_bytes(), aad="bad", alg=KEM_FOR_TESTS)

