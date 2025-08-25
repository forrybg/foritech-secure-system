#!/usr/bin/env bash
# setup.sh — bootstrap за Foritech SDK/API skeleton
set -euo pipefail

ts=$(date +%s)
backup_if_exists() {
  f="$1"
  if [ -e "$f" ]; then cp -f "$f" "$f.bak.$ts"; fi
}

# Директории
install -d foritech/crypto foritech/cli tests .github/workflows docs

# .gitignore
backup_if_exists .gitignore
cat > .gitignore <<'GIT'
__pycache__/
*.pyc
*.pyo
*.swp
.build/
dist/
*.egg-info/
.venv/
.env
.mypy_cache/
.pytest_cache/
.coverage
GIT

# pyproject.toml
backup_if_exists pyproject.toml
cat > pyproject.toml <<'TOML'
[project]
name = "foritech"
version = "0.1.0"
description = "Foritech SDK/API for PQC file wrap/unwrap with CLI"
readme = "README.md"
requires-python = ">=3.10"
authors = [{name="Foritech"}]
license = {text = "MIT"}
dependencies = [
  "typing-extensions>=4.6",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.8"]

[project.scripts]
foritech = "foritech.cli.main:main"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
TOML

# README.md
backup_if_exists README.md
cat > README.md <<'MD'
# Foritech

Скелет за стабилен SDK/API и CLI.
MD

# Минималните файлове
cat > foritech/__init__.py <<'PY'
__version__ = "0.1.0"
PY

cat > foritech/errors.py <<'PY'
class ForitechError(Exception): pass
class InvalidInput(ForitechError): pass
class CryptoBackendMissing(ForitechError): pass
class RecipientNotFound(ForitechError): pass
class IntegrityError(ForitechError): pass
class UnsupportedAlgorithm(ForitechError): pass
PY

cat > foritech/models.py <<'PY'
from dataclasses import dataclass, field
from typing import Optional, List, Union

@dataclass
class KemPolicy:
    algos: List[str] = field(default_factory=lambda: ["Kyber768"])
    prefer_ordered: bool = True
    require_pqc: bool = True

@dataclass
class WrapParams:
    kid: Optional[str] = None
    aad: Optional[bytes] = None
    kem_policy: KemPolicy = field(default_factory=KemPolicy)

@dataclass
class UnwrapParams:
    allow_fallback: bool = True

@dataclass
class WrapResult:
    kid: Optional[str]; nonce: Optional[str]; aad_present: bool; kem: str

@dataclass
class UnwrapResult:
    recovered_kid: Optional[str]; aad_present: bool; kem: str

@dataclass
class RawKemRecipient:
    public_key_path: str

@dataclass
class X509Recipient:
    pem_path: str

Recipient = Union[RawKemRecipient, X509Recipient]
PY

cat > foritech/api.py <<'PY'
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
PY

# CLI
cat > foritech/cli/__init__.py <<'PY'
# CLI package
PY

cat > foritech/cli/main.py <<'PY'
import argparse
from ..api import wrap_file, unwrap_file, detect_metadata
from ..models import WrapParams, KemPolicy, RawKemRecipient, X509Recipient
from ..errors import ForitechError

def _parse_recipient(r):
    if r.startswith("raw:"): return RawKemRecipient(public_key_path=r[4:])
    if r.startswith("x509:"): return X509Recipient(pem_path=r[5:])
    raise ForitechError(f"Unknown recipient: {r}")

def cmd_wrap(args):
    res = wrap_file(args.input, args.output, [_parse_recipient(r) for r in args.recipient],
                    WrapParams(kid=args.kid, aad=args.aad.encode() if args.aad else None,
                               kem_policy=KemPolicy([args.kem] if args.kem else ["Kyber768"])))
    print(f"OK wrap: {res}")

def cmd_unwrap(args):
    res = unwrap_file(args.input, args.output, None)
    print(f"OK unwrap: {res}")

def cmd_meta(args):
    meta = detect_metadata(args.input)
    print(f"Meta: {meta}")

def main(argv=None):
    p = argparse.ArgumentParser(prog="foritech")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("wrap"); w.add_argument("--in", dest="input", required=True)
    w.add_argument("--out", dest="output", required=True)
    w.add_argument("--recipient", action="append", required=True)
    w.add_argument("--kid"); w.add_argument("--aad"); w.add_argument("--kem")
    w.set_defaults(func=cmd_wrap)

    u = sub.add_parser("unwrap"); u.add_argument("--in", dest="input", required=True)
    u.add_argument("--out", dest="output", required=True)
    u.set_defaults(func=cmd_unwrap)

    m = sub.add_parser("meta"); m.add_argument("--in", dest="input", required=True)
    m.set_defaults(func=cmd_meta)

    args = p.parse_args(argv); args.func(args)

if __name__ == "__main__":
    main()
PY

# Тест
cat > tests/test_api_surface.py <<'PY'
from pathlib import Path
from foritech.api import wrap_file, unwrap_file
from foritech.models import WrapParams, RawKemRecipient

def test_wrap_unwrap(tmp_path: Path):
    src = tmp_path / "a.txt"; src.write_text("demo")
    enc = tmp_path / "a.enc"; out = tmp_path / "a.out"
    wrap_file(src, enc, [RawKemRecipient("dummy")], WrapParams())
    unwrap_file(enc, out, None)
    assert out.read_text() == "demo"
PY

# CI workflow
cat > .github/workflows/ci.yml <<'YML'
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix: { python-version: ["3.10","3.11","3.12","3.13"] }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}" }
      - run: pip install -e ".[dev]"
      - run: pytest -q
YML

# Документация
echo "# Quickstart" > docs/QUICKSTART.md

# Git commit
git add .
git commit -m "feat: bootstrap SDK/API skeleton"
echo "✅ Скелетът е готов. Стартирай: pip install -e ."
echo "После: foritech --help"
