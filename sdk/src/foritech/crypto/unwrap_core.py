from pathlib import Path; from typing import Any
from ..models import UnwrapParams
def unwrap_file(src: Path, dst: Path, params: UnwrapParams|None) -> dict[str, Any]:
    dst.write_bytes(Path(src).read_bytes()); return {"kid": None, "kem": "Kyber768", "aad_present": False}
def detect_metadata(src: Path) -> dict[str, Any]:
    return {"kid": None, "nonce": None, "kem": None, "aad_present": False}
