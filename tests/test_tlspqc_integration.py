import os, ssl, socket, time, subprocess, sys
from pathlib import Path
import pytest

from foritech.pki.x509_tools import generate_hybrid_selfsigned
from foritech.tlspqc import TLSPQCClient

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

need_sk  = Path.home()/".foritech/keys/kyber768_sec.bin"
need_pub = Path.home()/".foritech/keys/kyber768_pub.bin"

@pytest.mark.skipif(not need_sk.exists() or not need_pub.exists(), reason="need Kyber SK/PUB")
def test_tlspqc_session_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cert_pem, key_pem = generate_hybrid_selfsigned(
        "foritech-session", "Kyber768",
        (Path.home()/".foritech/keys/kyber768_pub.bin").read_bytes(),
        ext_format="spki"
    )
    cert = tmp_path/"cert.pem"; key = tmp_path/"key.pem"
    cert.write_bytes(cert_pem); key.write_bytes(key_pem)

    port = _free_port()
    env = os.environ.copy()
    env["FORITECH_SK"] = str(need_sk)

    srv = subprocess.Popen(
        [sys.executable, "scripts/tls_pqc_server.py",
         "--host","127.0.0.1","--port",str(port),
         "--cert",str(cert),"--key",str(key)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    # изчакай server TLS socket да се вдигне
    t0 = time.time(); ok = False
    while time.time()-t0 < 5:
        try:
            ctx = ssl._create_unverified_context()
            with socket.create_connection(("127.0.0.1", port), timeout=0.25) as raw:
                with ctx.wrap_socket(raw):
                    ok = True; break
        except Exception:
            time.sleep(0.1)
    assert ok, "server did not start"

    try:
        cli = TLSPQCClient("127.0.0.1", port, cafile=None)
        hs = cli.handshake()
        sess = cli.session(hs)

        plains, rotated = sess.send_many([b"m1", b"m2", b"m3"], key_update=False)
        assert [p.decode() for p in plains] == ["m1","m2","m3"]
        e0 = sess.epoch

        plains2, rotated2 = sess.send_many([b"m4", b"m5"], key_update=True)
        assert [p.decode() for p in plains2] == ["m4","m5"]
        assert rotated2 and sess.epoch == e0 + 1

        one, r3 = sess.send_one(b"last")
        assert one == b"last"

        assert sess.bye() is True
    finally:
        srv.terminate()
        try: srv.wait(timeout=3)
        except subprocess.TimeoutExpired: srv.kill()
