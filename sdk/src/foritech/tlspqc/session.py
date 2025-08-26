from __future__ import annotations
import ssl, socket, http.client, json, base64, os
from dataclasses import dataclass
from typing import List, Tuple, Optional

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305  # real import
from foritech.errors import ForitechError
from foritech.pki.x509_tools import extract_pqc_pub, extract_hybrid_info

INFO_BASE = b"foritech-kem-demo-v1"
AAD_BASE  = b"foritech-demo-session"

try:
    import oqs  # liboqs-python
except Exception as e:
    oqs = None

class TLSError(ForitechError):
    pass

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _aad_for_epoch(epoch: int) -> bytes:
    return AAD_BASE + b"|epoch=" + int(epoch).to_bytes(4, "big")

def _rotate(kek: bytes, epoch: int) -> bytes:
    info = b"foritech-keyupdate|epoch=" + int(epoch).to_bytes(4, "big")
    return _hkdf_32(kek, info)

def _post_json(host: str, port: int, path: str, obj: dict, cafile: Optional[str]):
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl._create_unverified_context()
    conn = http.client.HTTPSConnection(host, port, context=ctx)
    body = json.dumps(obj, separators=(",", ":")).encode()
    conn.request("POST", path, body=body, headers={"Content-Type":"application/json"})
    resp = conn.getresponse()
    data = resp.read()
    if resp.status != 200:
        raise TLSError(f"{path} status={resp.status} body={data!r}")
    return json.loads(data.decode())

def _fetch_server_cert(host: str, port: int, cafile: Optional[str]) -> bytes:
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl._create_unverified_context()
    with socket.create_connection((host, port)) as raw:
        with ctx.wrap_socket(raw, server_hostname=host if cafile else None) as ssock:
            der = ssock.getpeercert(binary_form=True)
            return ssl.DER_cert_to_PEM_cert(der).encode()

def _kem_encaps(pub: bytes):
    if oqs is None:
        raise TLSError("liboqs-python (module 'oqs') is required")
    with oqs.KeyEncapsulation("Kyber768") as kem:
        try:
            return kem.encap_secret(pub)
        except Exception:
            return kem.encap(pub)

@dataclass
class HandshakeResult:
    session_id: str
    epoch: int
    kek: bytes

class ClientSession:
    """
    Държи state (KEK + epoch) и говори към /send, /send-many, /bye.
    """
    def __init__(self, host: str, port: int, cafile: Optional[str], hs: HandshakeResult):
        self.host, self.port, self.cafile = host, port, cafile
        self.sid = hs.session_id
        self.kek = hs.kek
        self.epoch = hs.epoch

    def send_one(self, msg: bytes, key_update: bool = False) -> Tuple[bytes, bool]:
        aead = ChaCha20Poly1305(self.kek)
        nonce = os.urandom(12)
        enc = aead.encrypt(nonce, msg, _aad_for_epoch(self.epoch))
        out = _post_json(self.host, self.port, "/send", {
            "session_id": self.sid,
            "nonce_b64":  base64.b64encode(nonce).decode(),
            "enc_b64":    base64.b64encode(enc).decode(),
            "key_update": bool(key_update),
        }, self.cafile)
        plain = base64.b64decode(out["plaintext_b64"])
        rotated = bool(out.get("rotated", False))
        if rotated:
            next_epoch = int(out["next_epoch"])
            self.kek = _rotate(self.kek, self.epoch)
            self.epoch = next_epoch
        return plain, rotated

    def send_many(self, msgs: List[bytes], key_update: bool = False) -> Tuple[List[bytes], bool]:
        aead = ChaCha20Poly1305(self.kek)
        frames = []
        for m in msgs:
            n = os.urandom(12)
            c = aead.encrypt(n, m, _aad_for_epoch(self.epoch))
            frames.append({"nonce_b64": base64.b64encode(n).decode(),
                           "enc_b64":   base64.b64encode(c).decode()})
        out = _post_json(self.host, self.port, "/send-many", {
            "session_id": self.sid,
            "frames": frames,
            "key_update": bool(key_update),
        }, self.cafile)
        plains = [base64.b64decode(b) for b in out["plaintexts_b64"]]
        rotated = bool(out.get("rotated", False))
        if rotated:
            next_epoch = int(out["next_epoch"])
            self.kek = _rotate(self.kek, self.epoch)
            self.epoch = next_epoch
        return plains, rotated

    def bye(self) -> bool:
        out = _post_json(self.host, self.port, "/bye", {"session_id": self.sid}, self.cafile)
        return bool(out.get("deleted", False))

class TLSPQCClient:
    """
    High-level:
      client = TLSPQCClient(host, port, cafile=None)
      hs = client.handshake()  -> HandshakeResult
      sess = client.session(hs)
      sess.send_many([...], key_update=True)
    """
    def __init__(self, host: str, port: int, cafile: Optional[str] = None):
        self.host, self.port, self.cafile = host, port, cafile

    def handshake(self) -> HandshakeResult:
        pem = _fetch_server_cert(self.host, self.port, self.cafile)
        if not extract_hybrid_info(pem):
            raise TLSError("Server cert has no FORITECH hybrid extension")
        kem, pqc_pub = extract_pqc_pub(pem)
        ct, ss = _kem_encaps(pqc_pub)
        kek = _hkdf_32(ss, INFO_BASE)
        hs = _post_json(self.host, self.port, "/handshake", {"ct_b64": base64.b64encode(ct).decode()}, self.cafile)
        return HandshakeResult(session_id=hs["session_id"], epoch=int(hs.get("epoch", 0)), kek=kek)

    def session(self, hs: HandshakeResult) -> ClientSession:
        return ClientSession(self.host, self.port, self.cafile, hs)
