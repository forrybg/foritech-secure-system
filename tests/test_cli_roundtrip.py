import subprocess
import pytest
from pathlib import Path

PUB = Path.home() / ".foritech/keys/kyber768_pub.bin"
if not PUB.exists():
    pytest.skip("Kyber keypair not available (~/.foritech/keys).", allow_module_level=True)

def test_cli_roundtrip(tmp_path: Path):
    inp = tmp_path/"a.txt"; enc = tmp_path/"a.enc"; out = tmp_path/"a.out"
    inp.write_text("hello-cli")

    r1 = subprocess.run(
        ["foritech","wrap","--in",str(inp),"--out",str(enc),
         "--recipient", f"raw:{PUB}", "--kid","kid-777","--aad","demo"],
        text=True, capture_output=True, check=True
    )
    assert "OK:" in r1.stdout

    r2 = subprocess.run(["foritech","meta","--in",str(enc)], text=True, capture_output=True, check=True)
    assert "META:" in r2.stdout and "Kyber768" in r2.stdout and "AAD=True" in r2.stdout

    r3 = subprocess.run(["foritech","unwrap","--in",str(enc),"--out",str(out)], text=True, capture_output=True, check=True)
    assert "OK:" in r3.stdout
    assert out.read_text() == "hello-cli"
