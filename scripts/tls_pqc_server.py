from __future__ import annotations
import ssl
import json
import os
import base64
import argparse
import time
import threading
import collections
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

try:
    import oqs
except Exception as e:
    raise SystemExit("ERROR: liboqs-python (module 'oqs') is required") from e

INFO_BASE   = b"foritech-kem-demo-v1"
AAD_BASE    = b"foritech-demo-session"
TTL_SECONDS = 300       # 5 мин
SESSION_ID_BYTES = 16
ROTATE_EVERY = 32       # ротация след N съобщения, ако не е поискана по-рано
MAX_NONCES_PER_EPOCH = 4096  # прост лимит срещу nonce reuse/DoS

def _hkdf_32(secret: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(secret)

def _aad_for_epoch(epoch: int) -> bytes:
    return AAD_BASE + b"|epoch=" + epoch.to_bytes(4, "big")

def _rotate(kek: bytes, epoch: int) -> bytes:
    info = b"foritech-keyupdate|epoch=" + epoch.to_bytes(4, "big")
    return _hkdf_32(kek, info)

def _kem_decap(sk: bytes, ct: bytes) -> bytes:
    try:
        kem = oqs.KeyEncapsulation("Kyber768", secret_key=sk)
        decap = getattr(kem, "decap_secret", getattr(kem, "decap", None))
    except Exception:
        kem = oqs.KeyEncapsulation("Kyber768")
        try:
            kem.import_secret_key(sk)
        except Exception:
            pass
        decap = getattr(kem, "decap_secret", getattr(kem, "decap", None))
    if decap is None:
        raise RuntimeError("No decap method in oqs.KeyEncapsulation")
    return decap(ct)

class Handler(BaseHTTPRequestHandler):
    server_version = "ForitechTLS/3.0"

    def _json(self, code:int, obj:dict):
        data = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _get_sk(self) -> bytes:
        sk_path = self.server.kyber_sk
        if not sk_path or not os.path.exists(sk_path):
            raise RuntimeError(f"Kyber secret not found: {sk_path}")
        return open(sk_path, "rb").read()

    def _gc_sessions(self):
        now = time.time()
        with self.server.sess_lock:
            to_del = [sid for sid, s in self.server.sessions.items() if now - s["ts"] > TTL_SECONDS]
            for sid in to_del:
                self.server.sessions.pop(sid, None)

    def do_POST(self):
        self._gc_sessions()
        try:
            l = int(self.headers.get("Content-Length","0"))
            body = self.rfile.read(l)
            req = json.loads(body.decode("utf-8"))
        except Exception as e:
            return self._json(400, {"error": f"bad json: {e}"})

        # ---- /handshake: client -> ct_b64 ; server -> session_id, ttl ----
        if self.path == "/handshake":
            try:
                ct = base64.b64decode(req["ct_b64"])
                ss = _kem_decap(self._get_sk(), ct)
                kek = _hkdf_32(ss, INFO_BASE)
                sid = base64.urlsafe_b64encode(os.urandom(SESSION_ID_BYTES)).rstrip(b"=").decode()
                with self.server.sess_lock:
                    self.server.sessions[sid] = {
                        "kek": kek,
                        "epoch": 0,
                        "ts": time.time(),
                        "msg_count": 0,
                        "nonces": set(),
                        "nonces_order": collections.deque(maxlen=MAX_NONCES_PER_EPOCH),
                    }
                return self._json(200, {"session_id": sid, "ttl": TTL_SECONDS, "epoch": 0})
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # ---- /send: single frame {sid, nonce_b64, enc_b64} -> {plaintext_b64, rotated?, next_epoch?} ----
        if self.path == "/send":
            try:
                sid   = req["session_id"]
                nonce = base64.b64decode(req["nonce_b64"])
                enc   = base64.b64decode(req["enc_b64"])
                request_update = bool(req.get("key_update", False))
                with self.server.sess_lock:
                    sess = self.server.sessions.get(sid)
                    if not sess:
                        return self._json(404, {"error":"no such session"})
                    sess["ts"] = time.time()
                    kek   = sess["kek"]; epoch = sess["epoch"]
                    seen  = sess["nonces"]; order = sess["nonces_order"]
                    if nonce in seen:
                        return self._json(409, {"error":"nonce reuse"})
                aead = ChaCha20Poly1305(kek)
                plain = aead.decrypt(nonce, enc, _aad_for_epoch(epoch))
                with self.server.sess_lock:
                    # mark nonce and increase counters
                    seen.add(nonce); order.append(nonce)
                    sess["msg_count"] += 1
                    rotated = False
                    if request_update or sess["msg_count"] >= ROTATE_EVERY:
                        new_kek = _rotate(kek, epoch)
                        sess["kek"] = new_kek
                        sess["epoch"] = epoch + 1
                        sess["msg_count"] = 0
                        sess["nonces"].clear()
                        sess["nonces_order"].clear()
                        rotated = True
                        return self._json(200, {
                            "ok": True,
                            "plaintext_b64": base64.b64encode(plain).decode(),
                            "rotated": True,
                            "next_epoch": sess["epoch"],
                        })
                return self._json(200, {
                    "ok": True,
                    "plaintext_b64": base64.b64encode(plain).decode(),
                    "rotated": False,
                    "epoch": epoch,
                })
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # ---- /send-many: {sid, frames:[{nonce_b64,enc_b64}, ...], key_update?} ----
        if self.path == "/send-many":
            try:
                sid   = req["session_id"]
                frames = req.get("frames", [])
                request_update = bool(req.get("key_update", False))
                with self.server.sess_lock:
                    sess = self.server.sessions.get(sid)
                    if not sess:
                        return self._json(404, {"error":"no such session"})
                    sess["ts"] = time.time()
                    kek   = sess["kek"]; epoch = sess["epoch"]
                    seen  = sess["nonces"]; order = sess["nonces_order"]
                aead = ChaCha20Poly1305(kek)
                plains = []
                # decrypt all with current epoch/kek; reject any duplicate nonce
                for fr in frames:
                    nonce = base64.b64decode(fr["nonce_b64"])
                    if nonce in seen:
                        return self._json(409, {"error":"nonce reuse", "at": len(plains)})
                    enc   = base64.b64decode(fr["enc_b64"])
                    plain = aead.decrypt(nonce, enc, _aad_for_epoch(epoch))
                    plains.append(plain)
                # commit nonces and counters
                with self.server.sess_lock:
                    for fr in frames:
                        nonce = base64.b64decode(fr["nonce_b64"])
                        seen.add(nonce); order.append(nonce)
                    sess["msg_count"] += len(frames)
                    rotated = False
                    if request_update or sess["msg_count"] >= ROTATE_EVERY:
                        new_kek = _rotate(kek, epoch)
                        sess["kek"] = new_kek
                        sess["epoch"] = epoch + 1
                        sess["msg_count"] = 0
                        sess["nonces"].clear()
                        sess["nonces_order"].clear()
                        rotated = True
                        return self._json(200, {
                            "ok": True,
                            "count": len(plains),
                            "plaintexts_b64": [base64.b64encode(p).decode() for p in plains],
                            "rotated": True,
                            "next_epoch": sess["epoch"],
                        })
                return self._json(200, {
                    "ok": True,
                    "count": len(plains),
                    "plaintexts_b64": [base64.b64encode(p).decode() for p in plains],
                    "rotated": False,
                    "epoch": epoch,
                })
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # ---- /bye: drop session ----
        if self.path == "/bye":
            try:
                sid = req["session_id"]
                with self.server.sess_lock:
                    existed = self.server.sessions.pop(sid, None) is not None
                return self._json(200, {"deleted": existed})
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # legacy PoC (вече не се ползват)
        if self.path in ("/kem", "/kem-echo"):
            return self._json(410, {"error":"legacy endpoint; use /handshake, /send, /send-many, /bye"})

        return self._json(404, {"error":"not found"})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--cert", required=True)
    ap.add_argument("--key",  required=True)
    ap.add_argument("--kyber-sk", default=os.environ.get("FORITECH_SK"))
    args = ap.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.kyber_sk = args.kyber_sk
    httpd.sessions = {}     # sid -> {kek, epoch, ts, msg_count, nonces:set, nonces_order:deque}
    httpd.sess_lock = threading.Lock()

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=args.cert, keyfile=args.key)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"Server on https://{args.host}:{args.port}  (Kyber SK: {args.kyber_sk})")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
