from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import json, stat
from .crypto.pqc_kem import kem_generate, b64e, b64d
from .crypto.hybrid_wrap import hybrid_wrap_dek, hybrid_unwrap_dek

def generate_kem_keypair(alg: str = "ml-kem-768") -> Tuple[str, bytes]:
    pub, sec = kem_generate(alg)
    return b64e(pub), sec

def save_secret(path: str | Path, sec: bytes) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(sec)
    try: p.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception: pass

def load_pubjson(path: str | Path) -> Dict:
    return json.loads(Path(path).read_text())

def save_pubjson(path: str | Path, pub_b64: str, alg: str = "ml-kem-768", kid: str | None = None) -> None:
    obj = {"alg": alg, "pub_b64": pub_b64}
    if kid: obj["kid"] = kid
    Path(path).write_text(json.dumps(obj, indent=2))

def wrap_existing_dek_for(dek: bytes, recipients: List[Dict], aad: str = "", alg: str = "ml-kem-768") -> Dict:
    # Използваме същата логика като hybrid_wrap_dek, но вместо вътрешно генериран DEK използваме подадения.
    import os, json, hmac, hashlib
    from Crypto.Cipher import AES
    from .crypto.hybrid_wrap import hkdf, b64e, b64d, kem_encapsulate  # type: ignore
    aad_b = aad.encode()
    recipients_out = []
    for r in recipients:
        pub = b64d(r["pub_b64"])
        ct, shared = kem_encapsulate(pub, alg=alg)
        info = b"foritech-mlkem-wrap" + aad_b
        # HKDF за KEK
        kek = hkdf(salt=b"", ikm=shared, info=info, length=32)
        nonce = os.urandom(12)
        c = AES.new(kek, AES.MODE_GCM, nonce=nonce)
        c.update(aad_b)
        enc, tag = c.encrypt_and_digest(dek)
        recipients_out.append({
            "kid": r["kid"],
            "kem_ciphertext_b64": b64e(ct),
            "kem_pub_b64": r["pub_b64"],
            "nonce_b64": b64e(nonce),
            "tag_b64": b64e(tag),
            "enc_dek_b64": b64e(enc)
        })
    return {
        "version": 1,
        "sig_alg": "ml-dsa-44",
        "kem_alg": alg,
        "cipher": "AES-256-GCM",
        "aad": aad,
        "recipients": recipients_out
    }

def unwrap_dek(bundle: Dict, kid: str, sec_bytes: bytes, aad: str = "", alg: str = "ml-kem-768") -> bytes:
    return hybrid_unwrap_dek(bundle, recipient_kid=kid, sec_key=sec_bytes, kem_alg=alg, aad_str=aad)

def recipients_from_files(pubjson_paths: List[str | Path]) -> List[Dict]:
    out: List[Dict] = []
    for p in pubjson_paths:
        obj = load_pubjson(p)
        kid = obj.get("kid") or Path(p).stem
        out.append({"kid": kid, "pub_b64": obj["pub_b64"]})
    return out
