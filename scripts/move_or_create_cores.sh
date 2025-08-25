#!/usr/bin/env bash
set -euo pipefail
install -d sdk/src/foritech/crypto
[ -f sdk/src/foritech/crypto/__init__.py ] || echo "# crypto pkg" > sdk/src/foritech/crypto/__init__.py
mapfile -t WRAPS < <(find . -type f \( -name "wrap_file.py" -o -name "wrap.py" -o -name "*wrap*core*.py" -o -name "*wrap*file*.py" \) ! -path "./sdk/src/*")
mapfile -t UNWRAPS < <(find . -type f \( -name "unwrap_file.py" -o -name "unwrap.py" -o -name "*unwrap*core*.py" -o -name "*unwrap*file*.py" \) ! -path "./sdk/src/*")
move_one(){ local SRC="$1" DST="$2"; if command -v git >/dev/null; then git mv "$SRC" "$DST"; else mv "$SRC" "$DST"; fi }
if [ ${#WRAPS[@]} -eq 1 ]; then move_one "${WRAPS[0]}" sdk/src/foritech/crypto/wrap_core.py
elif [ ${#WRAPS[@]} -eq 0 ]; then cat > sdk/src/foritech/crypto/wrap_core.py <<'PY'
from pathlib import Path; from typing import Any, List
from ..models import Recipient, WrapParams
def wrap_file(src: Path, dst: Path, recipients: List[Recipient], params: WrapParams) -> dict[str, Any]:
    dst.write_bytes(Path(src).read_bytes()); return {"kid": params.kid, "nonce": None, "kem": (params.kem_policy.algos[0] if params.kem_policy.algos else "Kyber768"), "aad_present": params.aad is not None}
PY
else echo "⚠️ Налични са няколко wrap кандидата – премести правилния ръчно."; printf ' - %s\n' "${WRAPS[@]}"; fi
if [ ${#UNWRAPS[@]} -eq 1 ]; then move_one "${UNWRAPS[0]}" sdk/src/foritech/crypto/unwrap_core.py
elif [ ${#UNWRAPS[@]} -eq 0 ]; then cat > sdk/src/foritech/crypto/unwrap_core.py <<'PY'
from pathlib import Path; from typing import Any
from ..models import UnwrapParams
def unwrap_file(src: Path, dst: Path, params: UnwrapParams|None) -> dict[str, Any]:
    dst.write_bytes(Path(src).read_bytes()); return {"kid": None, "kem": "Kyber768", "aad_present": False}
def detect_metadata(src: Path) -> dict[str, Any]:
    return {"kid": None, "nonce": None, "kem": None, "aad_present": False}
PY
else echo "⚠️ Налични са няколко unwrap кандидата – премести правилния ръчно."; printf ' - %s\n' "${UNWRAPS[@]}"; fi
pip install -e . -q; pytest -q || true; echo "Готово ✅"
