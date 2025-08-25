import json, subprocess, sys, os, tempfile, pathlib

import os

import os
try:
    import oqs as _oqs
    _ENABLED_KEMS = set(getattr(_oqs, 'get_enabled_kems', lambda: [])())
except Exception:  # pragma: no cover
    _ENABLED_KEMS = set()
def _pick_kem_for_tests():
    env = os.environ.get('FORITECH_TEST_KEM')
    if env:
        return env
    if 'Kyber768' in _ENABLED_KEMS:
        return 'kyber768'
    return KEM_FOR_TESTS
KEM_FOR_TESTS = _pick_kem_for_tests()
try:
    import oqs as _oqs
    _ENABLED_KEMS = set(getattr(_oqs,'get_enabled_kems',lambda:[])())
except Exception:
    _ENABLED_KEMS = set()

def run_cli(*args):
    cmd = [sys.executable, "-m", "foritech.cli", *args]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

def test_cli_wrap_unwrap_roundtrip(tmp_path):
    # genkey
    base = tmp_path/"rk"
    run_cli("kem-genkey", "-k", KEM_FOR_TESTS, "-o", str(base))

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
