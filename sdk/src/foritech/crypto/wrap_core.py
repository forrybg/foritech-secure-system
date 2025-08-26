from __future__ import annotations
import os, json, base64, struct
from pathlib import Path
from typing import Any, List

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

try:
    import oqs  # pyoqs
except Exception:
    oqs = None

from ..models import Recipient, WrapParams, RawKemRecipient

MAGIC = b"FTECH"
VERSION = 1
AEAD = "CHACHA20-POLY1305"
KEM_NAME = "Kyber768"

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _load_pub(rec: RawKemRecipient) -> bytes:
    p = Path(rec.public_key_path)
    if not p.exists():
        raise FileNotFoundError(f"Recipient public key not found: {p}")
    return p.read_bytes()

def wrap_file(src: Path, dst: Path, recipients: List[Recipient], params: WrapParams) -> dict[str, Any]:
    """
    Формат:
      MAGIC(5) | VER(1) | HLEN(4 LE) | HEADER(JSON, HLEN) | CIPHERTEXT
    HEADER(JSON): { v, alg:{kem,aead}, kid, nonce, aad_b64?, recipients:[ {type,kem,ct,wrap_nonce,enc_dek,hint?}, ... ] }
    """
    if oqs is None:
        raise RuntimeError("pyoqs (liboqs bindings) is not installed. pip install pyoqs")

    pt = Path(src).read_bytes()
    dek = os.urandom(32)       # ChaCha20-Poly1305 key
    nonce = os.urandom(12)     # AEAD nonce за payload

    recs_meta: list[dict[str, Any]] = []
    for rec in recipients:
        if isinstance(rec, RawKemRecipient):
            pk = _load_pub(rec)
            with oqs.KeyEncapsulation(KEM_NAME) as kem:
                # pyoqs API: encap_secret(public_key) -> (ciphertext, shared_secret)
                try:
                    ct, ss = kem.encap_secret(pk)
                except Exception:
                    # по-стара/различна версия?
                    ct, ss = kem.encap(pk)  # fallback
            kek = _hkdf_32(ss, b"foritech-kek-v1")
            wrap_nonce = os.urandom(12)
            enc_dek = ChaCha20Poly1305(kek).encrypt(wrap_nonce, dek, None)
            recs_meta.append({
                "type": "raw",
                "kem": KEM_NAME,
                "ct": _b64(ct),
                "wrap_nonce": _b64(wrap_nonce),
                "enc_dek": _b64(enc_dek),
                "hint": os.path.basename(str(rec.public_key_path)),
            })

    header = {
        "v": VERSION,
        "alg": {"kem": KEM_NAME, "aead": AEAD},
        "kid": params.kid,
        "nonce": _b64(nonce),
        "aad_b64": _b64(params.aad) if params.aad is not None else None,
        "recipients": recs_meta,
    }
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")

    ciph = ChaCha20Poly1305(dek).encrypt(nonce, pt, header_json)  # bind header as AAD

    with open(dst, "wb") as f:
        f.write(MAGIC)
        f.write(bytes([VERSION]))
        f.write(struct.pack("<I", len(header_json)))
        f.write(header_json)
        f.write(ciph)

    return {"kid": params.kid, "nonce": header["nonce"], "kem": KEM_NAME, "aad_present": params.aad is not None}
