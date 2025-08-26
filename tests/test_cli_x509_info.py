from pathlib import Path
import subprocess

def test_cli_x509_info(tmp_path: Path):
    # dummy PQC pubkey (не е реален Kyber, но за extension не е важно)
    pqc_pub = b"dummy-pqc-pub"
    from foritech.pki.x509_tools import generate_hybrid_selfsigned
    cert_pem, key_pem = generate_hybrid_selfsigned("demo","Kyber768", pqc_pub)
    c = tmp_path/"cert.pem"; c.write_bytes(cert_pem)
    r = subprocess.run(["foritech","x509-info","--in",str(c)], capture_output=True, text=True)
    assert r.returncode == 0
    assert "X509: kem=Kyber768" in r.stdout
