from pathlib import Path
import json
import subprocess

def test_spki_json_and_extract(tmp_path: Path):
    pub = Path.home()/".foritech/keys/kyber768_pub.bin"
    assert pub.exists()
    cert = tmp_path/"spki_self.pem"
    key  = tmp_path/"spki_self.key"
    chain= tmp_path/"spki_chain.pem"
    r = subprocess.run([
        "foritech","x509-make","--cn","spki-demo","--format","spki",
        "--pqc-pub",str(pub),
        "--cert-out",str(cert),"--key-out",str(key),"--chain-out",str(chain)
    ], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout

    # JSON от info
    r = subprocess.run(["foritech","x509-info","--in",str(cert),"--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
    info = json.loads(r.stdout)
    assert info.get("format") == "spki-b64"
    assert info.get("kem") == "Kyber768"
    assert "spki_b64" in info and len(info["spki_b64"]) > 1000

    # extract и сравнение с raw kyber pub
    out = tmp_path/"pqc_spki.bin"
    r = subprocess.run(["foritech","x509-extract-pqc","--in",str(cert),"--out",str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
    data = out.read_bytes()
    assert len(data) == 1184  # Kyber768 public key size
    assert data == pub.read_bytes()
