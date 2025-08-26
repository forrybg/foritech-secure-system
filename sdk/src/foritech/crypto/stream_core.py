from __future__ import annotations
import base64
import os, json, base64, struct
from pathlib import Path
from typing import Any, List, BinaryIO, Optional

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

try:
    import oqs  # liboqs-python
except Exception:
    oqs = None

from ..models import Recipient, WrapParams, UnwrapParams, RawKemRecipient

MAGIC = b"FTECH"
VERSION = 1
AEAD = "CHACHA20-POLY1305"
KEM_NAME = "Kyber768"

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _b64d(s: str|bytes|None) -> bytes|None:
    if s is None: return None
    if isinstance(s, str): s = s.encode("ascii")
    return base64.b64decode(s)

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _wrap_recipients(dek: bytes, recipients: List[Recipient]) -> list[dict[str, Any]]:
    if oqs is None:
        raise RuntimeError("liboqs-python (module 'oqs') липсва. Инсталирай от GitHub.")
    recs: list[dict[str, Any]] = []
    for rec in recipients:
        if isinstance(rec, RawKemRecipient):
            pk = Path(rec.public_key_path).read_bytes()
            with oqs.KeyEncapsulation(KEM_NAME) as kem:
                try:
                    ct, ss = kem.encap_secret(pk)
                except Exception:
                    ct, ss = kem.encap(pk)
            kek = _hkdf_32(ss, b"foritech-kek-v1")
            wrap_nonce = os.urandom(12)
            enc_dek = ChaCha20Poly1305(kek).encrypt(wrap_nonce, dek, None)
            recs.append({
                "type": "raw", "kem": KEM_NAME,
                "ct": _b64(ct), "wrap_nonce": _b64(wrap_nonce), "enc_dek": _b64(enc_dek),
            })
    return recs

def _recover_dek(header: dict, secret_keys: list[bytes]) -> bytes:
    if oqs is None:
        raise RuntimeError("liboqs-python (module 'oqs') липсва.")
    for sk in secret_keys:
        # различни API варианти
        try:
            kem = oqs.KeyEncapsulation(KEM_NAME, secret_key=sk)
            decap = getattr(kem, "decap_secret", getattr(kem, "decap", None))
        except Exception:
            kem = oqs.KeyEncapsulation(KEM_NAME)
            try:
                kem.import_secret_key(sk)
            except Exception:
                pass
            decap = getattr(kem, "decap_secret", getattr(kem, "decap", None))
        if decap is None:
            continue
        for rec in header.get("recipients", []):
            if rec.get("kem") != KEM_NAME: continue
            ct = _b64d(rec["ct"])
            try:
                ss = decap(ct)
                kek = _hkdf_32(ss, b"foritech-kek-v1")
                wrap_nonce = _b64d(rec["wrap_nonce"])
                enc_dek = _b64d(rec["enc_dek"])
                dek = ChaCha20Poly1305(kek).decrypt(wrap_nonce, enc_dek, None)
                return dek
            except Exception:
                continue
    raise RuntimeError("Could not recover DEK via KEM")

def _iter_secret_keys() -> list[bytes]:
    out: list[bytes] = []
    import os
    from pathlib import Path
    env = os.environ.get("FORITECH_SK")
    if env and Path(env).exists():
        out.append(Path(env).read_bytes())
    default = Path(os.environ.get("FORITECH_KEYDIR", "~/.foritech/keys")).expanduser()
    if default.exists():
        for p in default.glob("*.bin"):
            try: out.append(p.read_bytes())
            except Exception: pass
    return out

def wrap_stream(reader: BinaryIO, writer: BinaryIO, recipients: List[Recipient], params: WrapParams, chunk_size: int = 1024*1024) -> dict[str, Any]:
    """
    Формат (streaming):
      MAGIC | VER | HLEN | HEADER_JSON | FRAMES...
    HEADER_JSON:
      { ..., "stream": {"chunk_size": <int>, "nonce8_b64": <b64>} }
    FRAME:
      idx(u32 LE) | clen(u32 LE) | ciphertext  (AEAD с nonce = nonce8||idx, AAD = HEADER_JSON + idx)
    """
    if chunk_size < 4096:
        chunk_size = 4096

    dek = os.urandom(32)
    recipients_meta = _wrap_recipients(dek, recipients)

    stream_nonce8 = os.urandom(8)
    header = {
        "v": VERSION,
        "alg": {"kem": KEM_NAME, "aead": AEAD},
        "kid": params.kid,
        "aad_b64": _b64(params.aad) if params.aad is not None else None,
        "recipients": recipients_meta,
        "stream": {"chunk_size": int(chunk_size), "nonce8_b64": _b64(stream_nonce8)},  # <- важно
    }
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")

    writer.write(MAGIC)
    writer.write(bytes([VERSION]))
    writer.write(struct.pack("<I", len(header_json)))
    writer.write(header_json)

    aead = ChaCha20Poly1305(dek)
    idx = 0
    while True:
        chunk = reader.read(chunk_size)
        if not chunk:
            break
        idx_le = struct.pack("<I", idx)
        nonce = stream_nonce8 + idx_le                     # 12-byte nonce
        aad   = header_json + idx_le
        ciph  = aead.encrypt(nonce, chunk, aad)

        writer.write(idx_le)
        writer.write(struct.pack("<I", len(ciph)))
        writer.write(ciph)                                  # <- не забравяй да запишеш ciphertext
        idx += 1

    return {"kid": params.kid, "aad_present": params.aad is not None, "kem": KEM_NAME, "stream": True, "chunk_size": chunk_size}

def unwrap_stream(reader: BinaryIO, writer: BinaryIO, params: Optional[UnwrapParams]) -> dict[str, Any]:
    # прочети header
    magic = reader.read(len(MAGIC))
    if magic != MAGIC:
        raise ValueError("Not a Foritech container (bad MAGIC)")
    ver = reader.read(1)
    if not ver:
        raise ValueError("Truncated header (no version)")
    hlen = struct.unpack("<I", reader.read(4))[0]
    header_json = reader.read(hlen)
    header = json.loads(header_json.decode("utf-8"))

    # ако няма 'stream', това не е streaming контейнер -> нека горният слой се погрижи
    if "stream" not in header:
        raise ValueError("Not a streaming container")

    stream = header["stream"]
    stream_nonce8 = _b64d(stream["nonce8"])
    # възстанови DEK
    sks = _iter_secret_keys()
    dek = _recover_dek(header, sks)
    aead = ChaCha20Poly1305(dek)

    # чети кадрите
    while True:
        idx_le = reader.read(4)
        if not idx_le:
            break
        clen_le = reader.read(4)
        if not clen_le:
            raise ValueError("Truncated frame length")
        clen = struct.unpack("<I", clen_le)[0]
        ciph = reader.read(clen)
        if len(ciph) != clen:
            raise ValueError("Truncated frame ciphertext")
        nonce = stream_nonce8 + idx_le
        aad = header_json + idx_le
        pt = aead.decrypt(nonce, ciph, aad)
        writer.write(pt)

    return {"kid": header.get("kid"), "kem": header.get("alg",{}).get("kem","Kyber768"), "aad_present": header.get("aad_b64") is not None}
