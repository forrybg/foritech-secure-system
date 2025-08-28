from __future__ import annotations
from pathlib import Path
import json
import struct

from .errors import ForitechError

# ── Реекспорт на ядрата (точни алиаси) ─────────────────────────────────────────
from .crypto.wrap_core import wrap_file as wrap_file
from .crypto.unwrap_core import unwrap_file as unwrap_file
from .crypto.stream_core import wrap_stream as wrap_stream
from .crypto.stream_core import unwrap_stream as unwrap_stream


def detect_metadata(src: str | Path):
    """Връща kid/nonce/AAD/KEM + STREAM/CHUNK (ако е стрийминг контейнер)."""
    from dataclasses import dataclass
    p = Path(src)
    if not p.exists():
        raise ForitechError(f"Input not found: {p}")

    @dataclass
    class Detected:
        kid: str | None
        nonce: str | None
        aad_present: bool
        kem: str | None
        stream: bool = False
        chunk_size: int | None = None

    with p.open("rb") as f:
        magic = f.read(5)
        if magic != b"FTECH":
            raise ForitechError("Not a Foritech container (bad MAGIC)")
        ver = f.read(1)
        if not ver:
            raise ForitechError("Truncated header (no version)")
        hlen = struct.unpack("<I", f.read(4))[0]
        header_json = f.read(hlen)

    hdr = json.loads(header_json.decode("utf-8"))
    kid = hdr.get("kid")
    kem = (hdr.get("alg") or {}).get("kem")
    aad_present = hdr.get("aad_b64") is not None
    nonce = hdr.get("nonce_b64") or hdr.get("nonce")
    s = hdr.get("stream") or {}
    return Detected(
        kid=kid,
        nonce=nonce,
        aad_present=aad_present,
        kem=kem,
        stream=bool(s),
        chunk_size=s.get("chunk_size"),
    )
