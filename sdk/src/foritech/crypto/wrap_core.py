from pathlib import Path; from typing import Any, List
from ..models import Recipient, WrapParams
def wrap_file(src: Path, dst: Path, recipients: List[Recipient], params: WrapParams) -> dict[str, Any]:
    dst.write_bytes(Path(src).read_bytes()); return {"kid": params.kid, "nonce": None, "kem": (params.kem_policy.algos[0] if params.kem_policy.algos else "Kyber768"), "aad_present": params.aad is not None}
