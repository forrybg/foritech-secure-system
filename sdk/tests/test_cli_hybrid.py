import json, subprocess, sys, os, tempfile, pathlib

def run_cli(*args):
    cmd = [sys.executable, "-m", "foritech.cli", *args]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

def test_cli_wrap_unwrap_roundtrip(tmp_path):
    # genkey
    base = tmp_path/"rk"
    run_cli("kem-genkey", "-k", "ml-kem-768", "-o", str(base))

    # recipients.json
    pubj = json.loads((base.with_suffix(".kem.pub.json")).read_text())
    recips = [
        {"kid":"ops-1", "pub_b64": pubj["pub_b64"]},
        {"kid":"dr-1", "pub_b64": pubj["pub_b64"]},
    ]
    recf = tmp_path/"recipients.json"
    recf.write_text(json.dumps(recips))

    # wrap
    bundlef = tmp_path/"bundle.json"
    run_cli("hybrid-wrap", "--recipients", str(recf), "--aad", "demo", "-o", str(bundlef))

    # unwrap
    outdek = tmp_path/"dek.bin"
    run_cli("hybrid-unwrap", "--secret", str(base.with_suffix(".kem.sec")), "--kid", "ops-1",
            "--bundle", str(bundlef), "--aad", "demo", "--out-dek", str(outdek))

    assert outdek.exists() and outdek.stat().st_size == 32
