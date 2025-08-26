from pathlib import Path
import pytest
from foritech.api import wrap_stream, unwrap_stream
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams

PUB = Path.home()/".foritech/keys/kyber768_pub.bin"
if not PUB.exists():
    pytest.skip("Kyber keypair not available (~/.foritech/keys).", allow_module_level=True)

def test_truncated_stream_frame(tmp_path: Path):
    inp = tmp_path/"a.txt"; enc = tmp_path/"a.enc"; out = tmp_path/"a.out"
    inp.write_bytes(b"A"*1024*1024 + b"B")  # >1MiB -> два фрейма
    with inp.open("rb") as r, enc.open("wb") as w:
        wrap_stream(r, w, [RawKemRecipient(str(PUB))], WrapParams(kid="kid-trunc", aad=b"x"))
    # отрежи последния байт
    raw = enc.read_bytes()
    enc.write_bytes(raw[:-1])
    with enc.open("rb") as r, out.open("wb") as w:
        with pytest.raises(Exception):
            unwrap_stream(r, w, UnwrapParams())
