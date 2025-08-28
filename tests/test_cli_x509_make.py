from pathlib import Path
import subprocess

def test_cli_x509_make(tmp_path: Path):
    pqc_pub = b"demo-pqc-pub"
    pp = tmp_path/"pqc.pub"; pp.write_bytes(pqc_pub)
    cert = tmp_path/"c.pem"; key = tmp_path/"k.pem"
    r = subprocess.run([
        "foritech","x509-make","--cn","demo",
        "--pqc-pub",str(pp),"--cert-out",str(cert),"--key-out",str(key)
    ], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
    assert cert.exists() and key.exists()
    # x509-info
    r2 = subprocess.run(["foritech","x509-info","--in",str(cert)], capture_output=True, text=True)
    assert r2.returncode == 0
    assert "X509: kem=" in r2.stdout
