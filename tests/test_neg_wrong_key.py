from pathlib import Path
import os, pytest
from foritech.api import wrap_file, unwrap_file
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams

PUB = Path.home()/".foritech/keys/kyber768_pub.bin"
SEC = Path.home()/".foritech/keys/kyber768_sec.bin"

if not PUB.exists() or not SEC.exists():
    pytest.skip("Kyber keypair not available.", allow_module_level=True)

def test_wrong_secret_key_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    inp = tmp_path/"a.txt"; enc = tmp_path/"a.enc"; out = tmp_path/"a.out"
    inp.write_text("hello")
    wrap_file(inp, enc, [RawKemRecipient(str(PUB))], WrapParams(kid="kid-wrong", aad=b"demo"))
    # насочи FORITECH_SK към несъществуващ/празен файл -> няма да може да възстанови DEK
    bad_sk = tmp_path/"bad_sk.bin"; bad_sk.write_bytes(b"\x00"*32)
    monkeypatch.setenv("FORITECH_SK", str(bad_sk))
    with pytest.raises(Exception):
        unwrap_file(enc, out, UnwrapParams())
