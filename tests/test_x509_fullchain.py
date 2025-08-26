from pathlib import Path
import subprocess

def test_issue_leaf_and_fullchain(tmp_path: Path):
    ca_cert = tmp_path/"ca.pem"
    ca_key  = tmp_path/"ca.key"
    r = subprocess.run(["foritech","x509-make-ca","--cn","demo-ca","--cert-out",str(ca_cert),"--key-out",str(ca_key)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout

    pub = Path.home()/".foritech/keys/kyber768_pub.bin"
    leaf = tmp_path/"leaf.pem"
    chain= tmp_path/"fullchain.pem"
    r = subprocess.run([
        "foritech","x509-issue","--cn","leaf","--kem","Kyber768","--format","spki",
        "--pqc-pub",str(pub),
        "--ca-cert",str(ca_cert),"--ca-key",str(ca_key),
        "--cert-out",str(leaf),"--chain-out",str(chain)
    ], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout

    # fullchain == leaf + CA
    assert chain.read_bytes() == leaf.read_bytes() + b"\n" + ca_cert.read_bytes()

    # OpenSSL verify
    r = subprocess.run(["openssl","verify","-CAfile",str(ca_cert), str(leaf)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
    assert "leaf.pem: OK" in r.stdout
