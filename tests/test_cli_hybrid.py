import os, sys, json, subprocess, tempfile, shutil
from pathlib import Path
import pytest

# Взимаме KEM от env или по подразбиране Kyber768 (широко поддържан)
KEM_FOR_TESTS = os.environ.get("FORITECH_TEST_KEM", "Kyber768")

def run_py(args, cwd=None):
    """Стартира с текущия Python интерпретатор (sys.executable), за да няма разминаване на среди."""
    cmd = [sys.executable] + args
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)

def test_cli_wrap_unwrap_roundtrip(tmp_path):
    # Генерираме два получателя
    a = tmp_path / "a"
    b = tmp_path / "b"
    run_py(["-m", "foritech.cli", "kem-genkey", "-k", KEM_FOR_TESTS, "-o", str(a)])
    run_py(["-m", "foritech.cli", "kem-genkey", "-k", KEM_FOR_TESTS, "-o", str(b)])

    # Примерен вход
    plain = tmp_path / "plain.txt"
    plain.write_text("hello-pqc")

    # wrap (ползва стабилни kid-ове в examples/wrap_file.py: ops-1, dr-1)
    out_enc   = tmp_path / "out.enc"
    out_bundle= tmp_path / "out.bundle.json"
    run_py([
        str((Path(__file__).parent.parent / "examples" / "wrap_file.py")),
        str(plain), str(out_enc), str(out_bundle), "demo-aad",
        str(a.with_suffix(".kem.pub.json")),
        str(b.with_suffix(".kem.pub.json")),
    ])

    # unwrap от първия получател (kid="ops-1")
    out_plain = tmp_path / "out.txt"
    run_py([
        str((Path(__file__).parent.parent / "examples" / "unwrap_file.py")),
        str(out_enc), str(out_bundle), str(out_plain), "demo-aad",
        "ops-1",
        str(a.with_suffix(".kem.sec")),
    ])

    assert out_plain.read_text() == "hello-pqc"
