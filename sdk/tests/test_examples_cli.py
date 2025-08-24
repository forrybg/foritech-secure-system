# sdk/tests/test_examples_cli.py
import subprocess, sys, tempfile
from pathlib import Path
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="example scripts tested only on unix-like env"
)

def test_examples_wrap_unwrap_roundtrip(tmp_path):
    sdk_dir = Path(__file__).resolve().parents[1]
    examples = sdk_dir / "examples"

    # 1) генерираме два ключа с foritech CLI
    subprocess.run(
        [sys.executable, "-m", "foritech.cli", "kem-genkey", "-k", "ml-kem-768", "-o", str(tmp_path/"a")],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "foritech.cli", "kem-genkey", "-k", "ml-kem-768", "-o", str(tmp_path/"b")],
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
