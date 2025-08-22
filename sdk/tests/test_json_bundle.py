import subprocess, shlex, json, os

def run(cmd: str):
    return subprocess.run(shlex.split(cmd), capture_output=True, text=True)

def test_json_bundle_roundtrip(tmp_path):
    out = tmp_path/"b.json"
    r1 = run(f"foritech hybrid-sign-json --data foritech-demo --alg Dilithium2 --out-file {out}")
    assert r1.returncode == 0
    assert out.exists()
    js = json.loads(out.read_text(encoding="utf-8"))
    assert js["alg"] == "Dilithium2"
    r2 = run(f"foritech hybrid-verify-json {out}")
    assert r2.returncode == 0
    assert "самолетът лети" in r2.stdout
