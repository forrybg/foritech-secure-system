from __future__ import annotations
import os
import json
import base64
import struct
from pathlib import Path
from typing import Any, Iterable, Optional

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

try:
    import oqs
except Exception:
    oqs = None

from ..models import UnwrapParams

MAGIC = b"FTECH"
KEM_NAME = "Kyber768"

def _b64d(s: str|bytes|None) -> bytes|None:
    if s is None: return None
    if isinstance(s, str): s = s.encode("ascii")
    return base64.b64decode(s)

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _iter_secret_keys() -> Iterable[bytes]:
    env = os.environ.get("FORITECH_SK")
    if env and Path(env).exists():
        yield Path(env).read_bytes()
    default = Path(os.environ.get("FORITECH_KEYDIR", "~/.foritech/keys")).expanduser()
    if default.exists():
        for p in default.glob("*.bin"):
            try: yield p.read_bytes()
            except Exception: continue

def _read_header_and_ciphertext(src: Path) -> tuple[dict[str, Any], bytes, bytes]:
    with open(src, "rb") as f:
        magic = f.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError("Not a Foritech container (bad MAGIC)")
        ver = f.read(1)
        if not ver:
            raise ValueError("Truncated header (no version)")
        hlen = struct.unpack("<I", f.read(4))[0]
        header_json = f.read(hlen)
        header = json.loads(header_json.decode("utf-8"))
        ciph = f.read()
    return header, header_json, ciph

def unwrap_file(src: Path, dst: Path, params: Optional[UnwrapParams]) -> dict[str, Any]:
    if oqs is None:
        raise RuntimeError("pyoqs (liboqs bindings) is not installed. pip install pyoqs")

    header, header_json, ciph = _read_header_and_ciphertext(src)
    nonce = _b64d(header.get("nonce"))
    recipients = header.get("recipients", [])

    dek: Optional[bytes] = None
    last_err: Optional[Exception] = None

    for sk in _iter_secret_keys():
        try:
            # pyoqs вариант 1: KeyEncapsulation(secret_key=sk)
            try:
                kem = oqs.KeyEncapsulation(KEM_NAME, secret_key=sk)
                decap = kem.decap_secret
            except Exception:
                # вариант 2: import_secret_key + decap/decap_secret
                kem = oqs.KeyEncapsulation(KEM_NAME)
                try:
                    kem.import_secret_key(sk)
                except Exception:
                    pass
                # името на метода може да е decap_secret или decap
                decap = getattr(kem, "decap_secret", getattr(kem, "decap", None))
                if decap is None:
                    raise RuntimeError("pyoqs decapsulation method not found")

            for rec in recipients:
                if rec.get("kem") != KEM_NAME:
                    continue
                ct = _b64d(rec["ct"])
                try:
                    ss = decap(ct)
                    kek = _hkdf_32(ss, b"foritech-kek-v1")
                    wrap_nonce = _b64d(rec["wrap_nonce"])
                    enc_dek = _b64d(rec["enc_dek"])
                    dek = ChaCha20Poly1305(kek).decrypt(wrap_nonce, enc_dek, None)
                    break
                except Exception as e:
                    last_err = e
                    continue
            if dek is not None:
                break
        except Exception as e:
            last_err = e
            continue

    if dek is None:
        raise RuntimeError(f"Could not recover DEK via KEM; last error: {last_err}")

    pt = ChaCha20Poly1305(dek).decrypt(nonce, ciph, header_json)
    Path(dst).write_bytes(pt)

    return {"kid": header.get("kid"), "kem": KEM_NAME, "aad_present": header.get("aad_b64") is not None}

def detect_metadata(src: Path) -> dict[str, Any]:
    header, _, _ = _read_header_and_ciphertext(src)
    return {
        "kid": header.get("kid"),
        "nonce": header.get("nonce"),
        "kem": header.get("alg", {}).get("kem"),
        "aad_present": header.get("aad_b64") is not None,
    }
