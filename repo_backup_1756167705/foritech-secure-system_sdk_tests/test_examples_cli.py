# --- CI header to ensure KEM_FOR_TESTS is defined early ---
import os
try:
    KEM_FOR_TESTS  # if already defined below, this won't raise
except NameError:
    def _pick_kem_for_tests():
        env = os.getenv("FORITECH_TEST_KEM")
        if env:
            return env
        try:
            import oqs
            enabled = set(getattr(oqs, "get_enabled_kem_mechanisms", lambda: [])())
            for cand in ("ml-kem-768", "ML-KEM-768", "Kyber768", "kyber768"):
                if cand in enabled:
                    return cand
        except Exception:
            pass
        return "Kyber768"
    KEM_FOR_TESTS = _pick_kem_for_tests()
# --- end header ---
# sdk/tests/test_examples_cli.py
import subprocess
import sys
from pathlib import Path
import pytest


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

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="example scripts tested only on unix-like env"
)

def test_examples_wrap_unwrap_roundtrip(tmp_path):
    sdk_dir = Path(__file__).resolve().parents[1]
    examples = sdk_dir / "examples"

    # 1) генерираме два ключа с foritech CLI
    subprocess.run(
        [sys.executable, "-m", "foritech.cli", "kem-genkey", "-k", KEM_FOR_TESTS, "-o", str(tmp_path/"a")],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "foritech.cli", "kem-genkey", "-k", KEM_FOR_TESTS, "-o", str(tmp_path/"b")],
        check=True,
    )

    # 2) подготвяме файл за криптиране
    plain_file = tmp_path / "plain.txt"
    plain_file.write_text("hello pqc examples")

    enc_file = tmp_path / "out.enc"
    bundle_file = tmp_path / "out.bundle.json"
    out_file = tmp_path / "out.txt"

    # 3) wrap_file.py
    subprocess.run(
        [sys.executable, str(examples/"wrap_file.py"),
         str(plain_file), str(enc_file), str(bundle_file),
         "demo-aad", str(tmp_path/"a.kem.pub.json"), str(tmp_path/"b.kem.pub.json")],
        check=True,
    )

    # 4) unwrap_file.py (само ops-1)
    subprocess.run(
        [sys.executable, str(examples/"unwrap_file.py"),
         str(enc_file), str(bundle_file), str(out_file),
         "demo-aad", "ops-1", str(tmp_path/"a.kem.sec")],
        check=True,
    )

    # 5) сравнение
    assert plain_file.read_bytes() == out_file.read_bytes()
