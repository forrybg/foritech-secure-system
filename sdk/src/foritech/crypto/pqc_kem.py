from __future__ import annotations

from base64 import b64encode, b64decode
from typing import Tuple
from oqs import KeyEncapsulation


# Алтернативни имена → официалните Kyber имена от liboqs
_ALG_ALIASES = {
    "ml-kem-512": "Kyber512",
    "ml-kem-768": "Kyber768",
    "ml-kem-1024": "Kyber1024",
    "ML-KEM-512": "Kyber512",
    "ML-KEM-768": "Kyber768",
    "ML-KEM-1024": "Kyber1024",
}


def normalize_alg(alg: str) -> str:
    """Приема ML-KEM алиаси и връща Kyber* име, което liboqs със сигурност поддържа."""
    return _ALG_ALIASES.get(alg, alg)


def b64e(b: bytes) -> str:
    """Encode bytes → base64 string (ASCII)."""
    return b64encode(b).decode("ascii")


def b64d(s: str) -> bytes:
    """Decode base64 string (ASCII) → bytes."""
    return b64decode(s.encode("ascii"))


def kem_generate(alg: str) -> Tuple[bytes, bytes]:
    """
    Generate a KEM keypair for algorithm `alg`.

    Returns:
        (pub, sec): public key bytes, secret key bytes
    """
    alg = normalize_alg(alg)
    with KeyEncapsulation(alg) as kem:
        pub = kem.generate_keypair()        # bytes
        sec = kem.export_secret_key()       # bytes
    return pub, sec


def kem_encapsulate(pub: bytes, alg: str) -> Tuple[bytes, bytes]:
    """
    Encapsulate to recipient public key `pub`.

    Returns:
        (ct, shared): ciphertext bytes, shared secret bytes
    """
    alg = normalize_alg(alg)
    with KeyEncapsulation(alg) as kem:
        ct, shared = kem.encap_secret(public_key=pub)
    return ct, shared


def kem_decapsulate(ct: bytes, sec: bytes, alg: str) -> bytes:
    """
    Decapsulate ciphertext `ct` using recipient secret key `sec`.

    Returns:
        shared: shared secret bytes
    """
    alg = normalize_alg(alg)
    with KeyEncapsulation(alg, secret_key=sec) as kem:
        shared = kem.decap_secret(ciphertext=ct)
    return shared
