from pathlib import Path
import pytest
from foritech.api import detect_metadata, wrap_file, unwrap_file
from foritech.models import WrapParams, RawKemRecipient

PUB = Path.home() / ".foritech/keys/kyber768_pub.bin"
if not PUB.exists():
    pytest.skip("Kyber keypair not available (~/.foritech/keys).", allow_module_level=True)

def test_meta_roundtrip(tmp_path: Path):
    inp = tmp_path / "a.txt"; out = tmp_path / "a.out"; enc = tmp_path / "a.enc"
    inp.write_text("hello")
    kid = "kid-test"
    res = wrap_file(inp, enc, [RawKemRecipient(str(PUB))], WrapParams(kid=kid, aad=b"demo"))
    meta = detect_metadata(enc)
    assert meta.kid == kid
    assert meta.kem == "Kyber768"
    assert meta.aad_present is True
    unwrap_file(enc, out, None)
    assert out.read_text() == "hello"
