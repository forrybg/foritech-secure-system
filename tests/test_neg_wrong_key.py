from pathlib import Path
import pytest
from foritech.api import wrap_stream, unwrap_stream
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams

PUB = Path.home()/".foritech/keys/kyber768_pub.bin"
SEC = Path.home()/".foritech/keys/kyber768_sec.bin"

if not PUB.exists() or not SEC.exists():
    pytest.skip("Kyber keypair not available.", allow_module_level=True)

def test_wrong_secret_key_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Стрийминг контейнер
    inp = tmp_path/"a.txt"; enc = tmp_path/"a.enc"; out = tmp_path/"a.out"
    inp.write_text("hello streaming")

    with inp.open("rb") as r, enc.open("wb") as w:
        wrap_stream(r, w, [RawKemRecipient(str(PUB))], WrapParams(kid="kid-wrong", aad=b"demo"))

    # Изолираме средата
    bad_sk = tmp_path/"bad_sk.bin"; bad_sk.write_bytes(b"\x00"*32)
    empty_keys = tmp_path/"EMPTY_KEYS"; empty_keys.mkdir()
    monkeypatch.setenv("FORITECH_SK", str(bad_sk))
    monkeypatch.setenv("FORITECH_KEYDIR", str(empty_keys))
    monkeypatch.setenv("HOME", str(tmp_path))

    with enc.open("rb") as r, out.open("wb") as w:
        with pytest.raises(Exception):
            unwrap_stream(r, w, UnwrapParams())
