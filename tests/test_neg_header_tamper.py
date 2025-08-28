from pathlib import Path
import json
import struct
import pytest
from foritech.api import wrap_stream, unwrap_stream
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams

PUB = Path.home()/".foritech/keys/kyber768_pub.bin"
if not PUB.exists():
    pytest.skip("Kyber keypair not available (~/.foritech/keys).", allow_module_level=True)

def tamper_header(p: Path):
    data = p.read_bytes()
    assert data[:5] == b"FTECH"
    ver = data[5:6]
    hlen = struct.unpack("<I", data[6:10])[0]
    header_json = data[10:10+hlen]
    rest = data[10+hlen:]
    hdr = json.loads(header_json.decode("utf-8"))
    # безопасна промяна със същия/подобен размер
    kid = (hdr.get("kid") or "kid") + "-tamper"
    hdr["kid"] = kid
    new_hdr = json.dumps(hdr, separators=(",",":")).encode("utf-8")
    new = b"FTECH" + ver + struct.pack("<I", len(new_hdr)) + new_hdr + rest
    p.write_bytes(new)

def test_stream_header_tamper_fails(tmp_path: Path):
    inp = tmp_path/"a.txt"; enc = tmp_path/"a.enc"; out = tmp_path/"a.out"
    inp.write_text("hello stream")
    with inp.open("rb") as r, enc.open("wb") as w:
        wrap_stream(r, w, [RawKemRecipient(str(PUB))], WrapParams(kid="kid-777", aad=b"demo"))
    tamper_header(enc)
    with enc.open("rb") as r, out.open("wb") as w:
        with pytest.raises(Exception):
            unwrap_stream(r, w, UnwrapParams())
