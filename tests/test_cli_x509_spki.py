from pathlib import Path
import subprocess
import shutil
import sys

def run(args):
    return subprocess.run(args, capture_output=True, text=True)

def test_cli_x509_make_spki(tmp_path: Path):
    pq = tmp_path/"pqc.pub"; pq.write_bytes(b"demo-pqc-pub")
    cert = tmp_path/"c.pem"; key = tmp_path/"k.pem"
    r = run(["foritech","x509-make","--cn","demo","--pqc-pub",str(pq),
             "--cert-out",str(cert),"--key-out",str(key),"--format","spki"])
    assert r.returncode == 0, r.stderr or r.stdout
    r2 = run(["foritech","x509-info","--in",str(cert)])
    assert r2.returncode == 0
    assert "format=spki-b64" in r2.stdout

def test_cli_x509_issue_spki(tmp_path: Path):
    ca_c = tmp_path/"ca.pem"; ca_k = tmp_path/"ca.key"
    r0 = run(["foritech","x509-make-ca","--cn","demo-ca",
              "--cert-out",str(ca_c),"--key-out",str(ca_k)])
    assert r0.returncode == 0, r0.stderr or r0.stdout

    pq = tmp_path/"pqc.pub"; pq.write_bytes(b"demo-pqc-pub")
    leaf = tmp_path/"leaf.pem"
    r = run(["foritech","x509-issue","--cn","leaf","--kem","Kyber768","--format","spki",
             "--pqc-pub",str(pq),"--ca-cert",str(ca_c),"--ca-key",str(ca_k),"--cert-out",str(leaf)])
    assert r.returncode == 0, r.stderr or r.stdout
    r2 = run(["foritech","x509-info","--in",str(leaf)])
    assert r2.returncode == 0
    assert "format=spki-b64" in r2.stdout
