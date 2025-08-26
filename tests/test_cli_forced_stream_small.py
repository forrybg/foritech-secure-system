from pathlib import Path
import subprocess, json, struct

def read_header(path: Path) -> dict:
    with path.open("rb") as f:
        assert f.read(5) == b"FTECH"
        f.read(1)  # ver
        hlen = struct.unpack("<I", f.read(4))[0]
        return json.loads(f.read(hlen).decode("utf-8"))

def test_forced_stream_small(tmp_path: Path):
    src = tmp_path / "s.txt"
    enc = tmp_path / "s.enc"
    src.write_text("x")

    pub = Path.home() / ".foritech/keys/kyber768_pub.bin"
    assert pub.exists(), "Missing Kyber public key"

    subprocess.run([
        "foritech", "wrap", "--stream",
        "--in", str(src), "--out", str(enc),
        "--recipient", f"raw:{pub}",
        "--kid", "kid-sf"
    ], check=True)

    hdr = read_header(enc)
    assert "stream" in hdr and isinstance(hdr["stream"], dict), "Missing stream section in header"
    assert "chunk_size" in hdr["stream"] and hdr["stream"]["chunk_size"] > 0
