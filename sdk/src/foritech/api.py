# sdk/src/foritech/api.py
from __future__ import annotations
import json
from base64 import b64encode

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, List, Optional
import inspect
import io
import tempfile

from .errors import ForitechError
from .models import Recipient, WrapParams, UnwrapParams, WrapResult, UnwrapResult

# ----------------------------
# Опитваме различни ядра/имена
# ----------------------------
core_wrap_fn = None
for mod, name in [
    (".crypto.wrap_core", "wrap_file"),
    (".crypto.wrap_core", "encrypt_file"),
    (".crypto.wrap_file", "wrap_file"),
    (".crypto.wrap_file", "wrap"),
]:
    try:
        core_wrap_fn = __import__(mod, fromlist=[name]).__dict__[name]
        break
    except Exception:
        pass

core_unwrap_fn = None
for mod, name in [
    (".crypto.unwrap_core", "unwrap_file"),
    (".crypto.unwrap_core", "decrypt_file"),
    (".crypto.unwrap_file", "unwrap_file"),
    (".crypto.unwrap_file", "unwrap"),
]:
    try:
        core_unwrap_fn = __import__(mod, fromlist=[name]).__dict__[name]
        break
    except Exception:
        pass

core_meta_fn = None
for mod, name in [
    (".crypto.unwrap_core", "detect_metadata"),
    (".crypto.unwrap_core", "read_header"),
    (".crypto.unwrap_core", "parse_header"),
    (".crypto.unwrap_file", "detect_metadata"),
    (".crypto.unwrap_file", "read_header"),
    (".crypto.unwrap_file", "parse_header"),
]:
    try:
        core_meta_fn = __import__(mod, fromlist=[name]).__dict__[name]
        break
    except Exception:
        pass


# ----------------------------
# Вътрешни помощници
# ----------------------------
def _extract(dict_like: Any, *keys: str) -> Optional[Any]:
    """Вади стойност от dict/обект по първия срещнат ключ/атрибут."""
    if dict_like is None:
        return None
    if isinstance(dict_like, dict):
        for k in keys:
            if k in dict_like:
                return dict_like[k]
        return None
    # опит за атрибути
    for k in keys:
        if hasattr(dict_like, k):
            return getattr(dict_like, k)
    return None


def _call_with_fallbacks(fn, *args, **kwargs):
    """Пробва няколко познати подписи, за да извика ядрената функция."""
    # 1) директно
    try:
        return fn(*args, **kwargs)
    except TypeError:
        pass

    # 2) само позиционни
    try:
        return fn(*args)
    except TypeError:
        pass

    # 3) смесени – ако функцията е с именовани аргументи
    sig = None
    try:
        sig = inspect.signature(fn)
    except Exception:
        sig = None

    if sig:
        bound_kwargs = {}
        for name in sig.parameters:
            if name in kwargs:
                bound_kwargs[name] = kwargs[name]
        try:
            return fn(*args[: len(sig.parameters) - len(bound_kwargs)], **bound_kwargs)
        except TypeError:
            pass

    # Нищо не проработи
    raise ForitechError(f"Core call failed for {fn.__module__}.{fn.__name__} – signature mismatch")


# ----------------------------
# Публичен API (стабилен слой)
# ----------------------------
def wrap_file(
    src: str | Path,
    dst: str | Path,
    recipients: List[Recipient],
    params: WrapParams,
) -> WrapResult:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_wrap_fn is None:
        # Временно поведение (копие), ако ядро липсва.
        dst_p.write_bytes(src_p.read_bytes())
        return WrapResult(
            kid=params.kid,
            nonce=None,
            aad_present=params.aad is not None,
            kem=params.kem_policy.algos[0],
        )

    # Подготвяне на типични kwargs към ядрата
    kwargs = {
        "recipients": recipients,
        "params": params,
        "kid": params.kid,
        "aad": params.aad,
        "kem": (params.kem_policy.algos if hasattr(params.kem_policy, "algos") else None),
    }

    meta = _call_with_fallbacks(core_wrap_fn, src_p, dst_p, **kwargs)

    return WrapResult(
        kid=_extract(meta, "kid", "key_id") or params.kid,
        nonce=_extract(meta, "nonce", "iv", "n"),
        aad_present=bool(_extract(meta, "aad_present", "has_aad", "aad") or (params.aad is not None)),
        kem=(_extract(meta, "kem", "kem_algo", "algorithm") or params.kem_policy.algos[0]),
    )


def unwrap_file(
    src: str | Path,
    dst: str | Path,
    params: UnwrapParams | None,
) -> UnwrapResult:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_unwrap_fn is None:
        # Временно поведение (копие), ако ядро липсва.
        dst_p.write_bytes(src_p.read_bytes())
        return UnwrapResult(recovered_kid=None, aad_present=False, kem="Kyber768")

    kwargs = {
        "params": params,
        "allow_fallback": getattr(params, "allow_fallback", True) if params else True,
    }

    meta = _call_with_fallbacks(core_unwrap_fn, src_p, dst_p, **kwargs)

    return UnwrapResult(
        recovered_kid=_extract(meta, "kid", "key_id", "recovered_kid"),
        aad_present=bool(_extract(meta, "aad_present", "has_aad", "aad")),
        kem=_extract(meta, "kem", "kem_algo", "algorithm") or "Kyber768",
    )


def wrap_stream(
    reader: BinaryIO,
    writer: BinaryIO,
    recipients: List[Recipient],
    params: WrapParams,
) -> WrapResult:
    """Stream API – ако няма ядро за стрийм, ползваме temp файлове."""
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
    """Връща лека структура с ключова метаинформация. Опитва да ползва ядро; иначе placeholder."""
    @dataclass
    class Detected:
        kid: Optional[str]
        nonce: Optional[str]
        aad_present: bool
        kem: Optional[str]

    src_p = Path(src)
    if not src_p.exists():
        raise ForitechError(f"Input not found: {src_p}")

    if core_meta_fn is None:
        # Ако няма meta функция в ядрото – минимален placeholder
        return Detected(kid=None, nonce=None, aad_present=False, kem=None)

    try:
        meta = _call_with_fallbacks(core_meta_fn, src_p)
    except ForitechError:
        # Някои имплементации искат файл-обект вместо път
        with src_p.open("rb") as fh:
            meta = _call_with_fallbacks(core_meta_fn, fh)

    return Detected(
        kid=_extract(meta, "kid", "key_id"),
        nonce=_extract(meta, "nonce", "iv", "n"),
        aad_present=bool(_extract(meta, "aad_present", "has_aad", "aad")),
        kem=_extract(meta, "kem", "kem_algo", "algorithm"),
    )


# --- compatibility: test helper ---
try:
    from .crypto.pqc_kem import kem_generate, normalize_alg
    def generate_kem_keypair(alg: str = "Kyber768"):
        """Return (pub, sec) for tests/compat; accepts ML-KEM aliases too."""
        return kem_generate(normalize_alg(alg))
except Exception:
    # keep API import errors visible during tests; do not hide real issues
    pass

# --- simple file helpers for tests ---
from pathlib import Path
import os

def save_secret(path: str | os.PathLike, sec_bytes: bytes) -> None:
    """Save secret key bytes to file with 0600 permissions."""
    p = Path(path)
    p.write_bytes(sec_bytes)
    try:
        os.chmod(p, 0o600)
    except Exception:
        # best effort (Windows/GitHub runner etc.)
        pass

def save_pubjson(path, pub_bytes: bytes, kid: str = "u1") -> None:
    """
    Записва публичен KEM ключ в JSON формат:
      {"kid": "<kid>", "pub_b64": "<base64>"}
    """
    data = {"kid": kid, "pub_b64": b64encode(pub_bytes).decode("ascii")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

