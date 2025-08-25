from pathlib import Path
from foritech.api import wrap_file, unwrap_file
from foritech.models import WrapParams, RawKemRecipient

def test_wrap_unwrap(tmp_path: Path):
    src = tmp_path / "a.txt"; src.write_text("demo")
    enc = tmp_path / "a.enc"; out = tmp_path / "a.out"
    wrap_file(src, enc, [RawKemRecipient("dummy")], WrapParams())
    unwrap_file(enc, out, None)
    assert out.read_text() == "demo"
