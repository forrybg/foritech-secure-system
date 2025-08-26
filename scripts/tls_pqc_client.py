from __future__ import annotations
import ssl, socket, base64, json, argparse, http.client, os
from typing import List, Tuple

try:
    import oqs
except Exception as e:
    raise SystemExit("ERROR: liboqs-python (module 'oqs') is required on client") from e

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from foritech.pki.x509_tools import extract_pqc_pub, extract_hybrid_info

INFO_BASE = b"foritech-kem-demo-v1"
AAD_BASE  = b"foritech-demo-session"

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _aad_for_epoch(epoch: int) -> bytes:
    return AAD_BASE + b"|epoch=" + epoch.to_bytes(4, "big")

def _rotate(kek: bytes, epoch: int) -> bytes:
    info = b"foritech-keyupdate|epoch=" + epoch.to_bytes(4, "big")
    return _hkdf_32(kek, info)

def fetch_server_cert(host: str, port: int, cafile: str|None):
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl._create_unverified_context()
    with socket.create_connection((host, port)) as raw:
        with ctx.wrap_socket(raw, server_hostname=host if cafile else None) as ssock:
            der = ssock.getpeercert(binary_form=True)
            return ssl.DER_cert_to_PEM_cert(der).encode()

def kem_encaps(pub: bytes):
    with oqs.KeyEncapsulation("Kyber768") as kem:
        try:
            return kem.encap_secret(pub)
        except Exception:
            return kem.encap(pub)

def post_json(host: str, port: int, path: str, obj: dict, cafile: str|None):
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl._create_unverified_context()
    conn = http.client.HTTPSConnection(host, port, context=ctx)
    body = json.dumps(obj, separators=(",", ":")).encode()
    conn.request("POST", path, body=body, headers={"Content-Type":"application/json"})
    resp = conn.getresponse()
    data = resp.read()
    if resp.status != 200:
        raise RuntimeError(f"{path} status={resp.status} body={data!r}")
    return json.loads(data.decode())

class Session:
    def __init__(self, host:str, port:int, cafile:str|None, kek:bytes, sid:str, epoch:int=0):
        self.host = host; self.port = port; self.cafile = cafile
        self.kek = kek; self.epoch = epoch

    def send_one(self, msg: bytes, key_update: bool=False) -> Tuple[bytes, bool]:
        aead = ChaCha20Poly1305(self.kek)
        nonce = os.urandom(12)
        enc = aead.encrypt(nonce, msg, _aad_for_epoch(self.epoch))
        out = post_json(self.host, self.port, "/send", {
            "session_id": self.sid,
            "nonce_b64":  base64.b64encode(nonce).decode(),
            "enc_b64":    base64.b64encode(enc).decode(),
            "key_update": key_update,
        }, self.cafile)
        plain = base64.b64decode(out["plaintext_b64"])
        rotated = bool(out.get("rotated", False))
        if rotated:
            next_epoch = int(out["next_epoch"])
            # derive new key from our current (pre-rotation) kek
            self.kek = _rotate(self.kek, self.epoch)
            self.epoch = next_epoch
        return plain, rotated

    def send_many(self, msgs: List[bytes], key_update: bool=False) -> Tuple[List[bytes], bool]:
        aead = ChaCha20Poly1305(self.kek)
        frames = []
        for m in msgs:
            n = os.urandom(12)
            c = aead.encrypt(n, m, _aad_for_epoch(self.epoch))
            frames.append({
                "nonce_b64": base64.b64encode(n).decode(),
                "enc_b64":   base64.b64encode(c).decode(),
            })
        out = post_json(self.host, self.port, "/send-many", {
            "session_id": self.sid,
            "frames": frames,
            "key_update": key_update,
        }, self.cafile)
        plains = [base64.b64decode(b) for b in out["plaintexts_b64"]]
        rotated = bool(out.get("rotated", False))
        if rotated:
            next_epoch = int(out["next_epoch"])
            self.kek = _rotate(self.kek, self.epoch)
            self.epoch = next_epoch
        return plains, rotated

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--cafile", default=None)
    args = ap.parse_args()

    # 1) вземи cert-а и PQC ключа
    pem = fetch_server_cert(args.host, args.port, args.cafile)
    if not extract_hybrid_info(pem):
        raise SystemExit("Server cert has no FORITECH hybrid extension")
    kem, pqc_pub = extract_pqc_pub(pem)
    print(f"Server KEM: {kem}, pub={len(pqc_pub)} bytes")

    # 2) handshake -> kek + sid
    ct, ss = kem_encaps(pqc_pub)
    kek = _hkdf_32(ss, INFO_BASE)
    hs = post_json(args.host, args.port, "/handshake", {"ct_b64": base64.b64encode(ct).decode()}, args.cafile)
    sid = hs["session_id"]; epoch = int(hs.get("epoch", 0))
    print("session_id:", sid, "epoch:", epoch)

    sess = Session(args.host, args.port, args.cafile, kek, sid, epoch)
    # inject sid (малка хитрина за по-прост конструктор)
    Session.sid = property(lambda self: sid)

    # 3) batch #1
    msgs = [b"m1", b"m2", b"m3"]
    plains, rotated = sess.send_many(msgs, key_update=False)
    print("Batch1:", [p.decode() for p in plains], "rotated?", rotated, "epoch:", sess.epoch)

    # 4) batch #2 + искане за key update
    msgs2 = [b"m4", b"m5"]
    plains2, rotated2 = sess.send_many(msgs2, key_update=True)
    print("Batch2:", [p.decode() for p in plains2], "rotated?", rotated2, "epoch:", sess.epoch)

    # 5) single
    p3, rot3 = sess.send_one(b"last-one", key_update=False)
    print("Single:", p3.decode(), "rotated?", rot3, "epoch:", sess.epoch)

    # 6) bye
    bye = post_json(args.host, args.port, "/bye", {"session_id": sid}, args.cafile)
    print("Session deleted:", bye["deleted"])
    print("OK ✅")

if __name__ == "__main__":
    main()
