from pathlib import Path, subprocess
import json, struct

def read_header(path: Path):
    with path.open("rb") as f:
        assert f.read(5) == b"FTECH"
        f.read(1)
        hlen = struct.unpack("<I", f.read(4))[0]
        return json.loads(f.read(hlen).decode("utf-8"))

def test_forced_stream_small(tmp_path: Path):
    src = tmp_path/"s.txt"; src.write_text("x")
    enc = tmp_path/"s.enc"
    from pathlib import Path as P; pub = P.home()/".foritech/keys/kyber768_pub.bin"
    assert pub.exists()
    import subprocess
    subprocess.check_call(["foritech","wrap","--stream","--in",str(src),"--out",str(enc),"--recipient",f"raw:{pub}","--kid","kid-sf"])
    hdr = read_header(enc)
    assert "stream" in hdr and "chunk_size" in hdr["stream"]
