# sdk/src/foritech/api.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, List, Optional
import tempfile

from .errors import ForitechError
from .models import Recipient, WrapParams, UnwrapParams, WrapResult, UnwrapResult

# --- Твърди импорти към ядрата (вече съществуват) ---
try:
    from .crypto.wrap_core import wrap_file as core_wrap_file  # type: ignore
except Exception as e:
    core_wrap_file = None  # ще обясним по-долу

try:
    from .crypto.unwrap_core import (
        unwrap_file as core_unwrap_file,       # type: ignore
        detect_metadata as core_detect_metadata,  # type: ignore
    )
except Exception:
    core_unwrap_file = None
    core_detect_metadata = None


def wrap_file(
    src: str | Path,
    dst: str | Path,
    recipients: List[Recipient],
    params: WrapParams,
) -> WrapResult:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_wrap_file is None:
        # Ако тук влезеш – значи няма ядро. За да не те лъжем, гръмваме с ясно съобщение:
        raise ForitechError("Crypto core not wired (foritech.crypto.wrap_core.wrap_file is missing)")

    meta = core_wrap_file(src_p, dst_p, recipients, params)  # очакваме dict или обект с полета

    # Попълване на WrapResult
    kid = getattr(meta, "kid", None) if meta is not None else None
    if isinstance(meta, dict):
        kid = meta.get("kid", kid)
        nonce = meta.get("nonce", None)
        kem = meta.get("kem", None)
        aad_present = bool(meta.get("aad_present", params.aad is not None))
    else:
        nonce = getattr(meta, "nonce", None)
        kem = getattr(meta, "kem", None)
        aad_present = bool(getattr(meta, "aad_present", params.aad is not None))

    return WrapResult(
        kid=kid if kid is not None else params.kid,
        nonce=nonce,
        aad_present=aad_present,
        kem=kem if kem is not None else (params.kem_policy.algos[0] if params.kem_policy.algos else "Kyber768"),
    )


def unwrap_file(
    src: str | Path,
    dst: str | Path,
    params: Optional[UnwrapParams],
) -> UnwrapResult:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_unwrap_file is None:
        raise ForitechError("Crypto core not wired (foritech.crypto.unwrap_core.unwrap_file is missing)")

    meta = core_unwrap_file(src_p, dst_p, params)

    if isinstance(meta, dict):
        return UnwrapResult(
            recovered_kid=meta.get("kid"),
            aad_present=bool(meta.get("aad_present", False)),
            kem=meta.get("kem", "Kyber768"),
        )
    return UnwrapResult(
        recovered_kid=getattr(meta, "kid", None),
        aad_present=bool(getattr(meta, "aad_present", False)),
        kem=getattr(meta, "kem", "Kyber768"),
    )


def wrap_stream(
    reader: BinaryIO,
    writer: BinaryIO,
    recipients: List[Recipient],
    params: WrapParams,
) -> WrapResult:
    with tempfile.TemporaryDirectory() as td:
        tmp_in = Path(td) / "in.bin"
        tmp_out = Path(td) / "out.bin"
        data = reader.read()
        if isinstance(data, str):
            data = data.encode()
        tmp_in.write_bytes(data)
        res = wrap_file(tmp_in, tmp_out, recipients, params)
        writer.write(tmp_out.read_bytes())
    return res


def unwrap_stream(reader: BinaryIO, writer: BinaryIO, params: UnwrapParams) -> UnwrapResult:
    with tempfile.TemporaryDirectory() as td:
        tmp_in = Path(td) / "in.enc"
        tmp_out = Path(td) / "out.dec"
        data = reader.read()
        if isinstance(data, str):
            data = data.encode()
        tmp_in.write_bytes(data)
        res = unwrap_file(tmp_in, tmp_out, params)
        writer.write(tmp_out.read_bytes())
    return res


def detect_metadata(src: str | Path):
    @dataclass
    class Detected:
        kid: Optional[str]
        nonce: Optional[str]
        aad_present: bool
        kem: Optional[str]

    src_p = Path(src)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_detect_metadata is None:
        # Няма ядро за meta – връщаме минимален placeholder (по-добре отколкото да паднем)
        return Detected(kid=None, nonce=None, aad_present=False, kem=None)

    meta = core_detect_metadata(src_p)
    if isinstance(meta, dict):
        return Detected(
            kid=meta.get("kid"),
            nonce=meta.get("nonce"),
            aad_present=bool(meta.get("aad_present", False)),
            kem=meta.get("kem"),
        )
    # ако е обект с атрибути
    return Detected(
        kid=getattr(meta, "kid", None),
        nonce=getattr(meta, "nonce", None),
        aad_present=bool(getattr(meta, "aad_present", False)),
        kem=getattr(meta, "kem", None),
    )
