from pathlib import Path
from typing import List, BinaryIO
from .errors import ForitechError
from .models import Recipient, WrapParams, UnwrapParams, WrapResult, UnwrapResult

def wrap_file(src: str|Path, dst: str|Path, recipients: List[Recipient], params: WrapParams) -> WrapResult:
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise ForitechError(f"Input not found: {src}")
    dst.write_bytes(src.read_bytes())  # временно copy
    return WrapResult(kid=params.kid, nonce=None, aad_present=params.aad is not None, kem=params.kem_policy.algos[0])

def unwrap_file(src: str|Path, dst: str|Path, params: UnwrapParams|None) -> UnwrapResult:
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise ForitechError(f"Input not found: {src}")
    dst.write_bytes(src.read_bytes())
    return UnwrapResult(recovered_kid=None, aad_present=False, kem="Kyber768")

def wrap_stream(reader: BinaryIO, writer: BinaryIO, recipients: List[Recipient], params: WrapParams) -> WrapResult:
    data = reader.read(); writer.write(data)
    return WrapResult(kid=params.kid, nonce=None, aad_present=params.aad is not None, kem=params.kem_policy.algos[0])

def unwrap_stream(reader: BinaryIO, writer: BinaryIO, params: UnwrapParams) -> UnwrapResult:
    data = reader.read(); writer.write(data)
    return UnwrapResult(recovered_kid=None, aad_present=False, kem="Kyber768")

def detect_metadata(src: str|Path):
    from dataclasses import dataclass
    @dataclass
    class Detected: kid:str|None; nonce:str|None; aad_present:bool; kem:str|None
    return Detected(None,None,False,None)
