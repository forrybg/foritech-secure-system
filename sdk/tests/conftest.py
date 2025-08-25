import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
src = root / "src"

def _ensure_on_path(p: Path):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

if (src / "foritech").exists():
    _ensure_on_path(src)
elif (root / "foritech").exists():
    _ensure_on_path(root)
