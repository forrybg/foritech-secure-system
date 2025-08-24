import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]  # <repo>/sdk
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
