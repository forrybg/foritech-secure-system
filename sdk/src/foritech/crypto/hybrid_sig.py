try:
    import oqs
    _HAS_OQS = True
except Exception:
    oqs = None
    _HAS_OQS = False

from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives import hashes


class HybridSignature:
    """
    Хибриден подпис: RSA + PQC (напр. Dilithium2) за API:
      - generate_keypair() -> bytes (public key)
      - sign(msg) -> bytes
      - verify(msg, sig, public_key) -> bool
    Държим една "signer" инстанция (с вътрешен таен ключ) и пазим публичния ключ (bytes).
    """

    def __init__(self, pqc_alg: str = "Dilithium2"):
        if not _HAS_OQS:
            raise RuntimeError("Не е инсталиран oqs (liboqs-python).")
        self._pqc_alg = pqc_alg

        # RSA
        self._rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # PQC signer (държим жива инстанция с таен ключ вътре)
        try:
            self._pqc_signer = oqs.Signature(self._pqc_alg)
            self._pqc_pk = self._pqc_signer.generate_keypair()  # bytes (public key)
            if not isinstance(self._pqc_pk, (bytes, bytearray)):
                raise RuntimeError("generate_keypair() не върна bytes публичен ключ.")
        except Exception as e:
            raise RuntimeError("Неуспешна инициализация на PQC подписвач/ключове.") from e

    @property
    def pqc_public_key(self) -> bytes:
        return self._pqc_pk

    @property
    def rsa_public_key(self):
        return self._rsa.public_key()

    def sign(self, msg: bytes) -> dict:
        sig_rsa = self._rsa.sign(msg, rsa_padding.PKCS1v15(), hashes.SHA256())
        sig_pqc = self._pqc_signer.sign(msg)
        return {"rsa": sig_rsa, "pqc": sig_pqc}

    def verify(self, msg: bytes, sigs: dict) -> bool:
        # RSA verify
        try:
            self._rsa.public_key().verify(
                sigs["rsa"], msg, rsa_padding.PKCS1v15(), hashes.SHA256()
            )
            ok_rsa = True
        except Exception:
            ok_rsa = False

        # PQC verify — според твоя API: verify(message, signature, public_key)
        try:
            with oqs.Signature(self._pqc_alg) as v:
                ok_pqc = v.verify(msg, sigs["pqc"], self._pqc_pk)
        except Exception:
            ok_pqc = False

        return ok_rsa and ok_pqc


def verify_with_keys(msg: bytes, rsa_public_key, pqc_alg: str, pqc_public_key: bytes, sigs: dict) -> bool:
    # RSA
    try:
        rsa_public_key.verify(
            sigs["rsa"], msg, rsa_padding.PKCS1v15(), hashes.SHA256()
        )
        ok_rsa = True
    except Exception:
        ok_rsa = False

    # PQC
    try:
        with oqs.Signature(pqc_alg) as v:
            ok_pqc = v.verify(msg, sigs["pqc"], pqc_public_key)
    except Exception:
        ok_pqc = False

    return ok_rsa and ok_pqc
