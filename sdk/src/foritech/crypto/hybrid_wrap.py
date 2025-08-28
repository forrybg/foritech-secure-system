import os
import json
import hmac
import hashlib
from typing import List, Dict, Tuple
from Crypto.Cipher import AES
from .pqc_kem import kem_encapsulate, kem_decapsulate, b64e, b64d

def hkdf_extract(salt: bytes, ikm: bytes, hash=hashlib.sha256) -> bytes:
    return hmac.new(salt or b"\x00"*hash().digest_size, ikm, hash).digest()

def hkdf_expand(prk: bytes, info: bytes, length: int, hash=hashlib.sha256) -> bytes:
    n = (length + hash().digest_size - 1) // hash().digest_size
    okm, t = b"", b""
    for i in range(1, n+1):
        t = hmac.new(prk, t + info + bytes([i]), hash).digest()
        okm += t
    return okm[:length]

def hkdf(salt: bytes, ikm: bytes, info: bytes, length: int=32) -> bytes:
    return hkdf_expand(hkdf_extract(salt, ikm), info, length)

def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: bytes=b"") -> Tuple[bytes, bytes, bytes]:
    nonce = os.urandom(12)
    c = AES.new(key, AES.MODE_GCM, nonce=nonce)
    c.update(aad)
    enc, tag = c.encrypt_and_digest(plaintext)
    return nonce, enc, tag

def hybrid_wrap_dek(pubkeys: List[Dict], kem_alg="ml-kem-768", aad_str="", signer=None) -> Dict:
    dek = os.urandom(32)  # 256-bit
    aad = aad_str.encode()
    recipients_out = []
    for r in pubkeys:
        pub = b64d(r["pub_b64"])
        ct, shared = kem_encapsulate(pub, alg=kem_alg)
        info = b"foritech-mlkem-wrap" + aad
        kek = hkdf(salt=b"", ikm=shared, info=info, length=32)
        nonce, enc_dek, tag = aes_gcm_encrypt(kek, dek, aad=aad)
        recipients_out.append({
            "kid": r["kid"],
            "kem_ciphertext_b64": b64e(ct),
            "kem_pub_b64": r["pub_b64"],
            "nonce_b64": b64e(nonce),
            "tag_b64": b64e(tag),
            "enc_dek_b64": b64e(enc_dek)
        })
    bundle = {
        "version": 1,
        "sig_alg": getattr(signer, "alg", None) or "ml-dsa-44",
        "kem_alg": kem_alg,
        "cipher": "AES-256-GCM",
        "aad": aad_str,
        "recipients": recipients_out
    }
    if signer is not None:
        to_sign = json.dumps(bundle, separators=(",", ":"), sort_keys=True).encode()
        signature = signer.sign(to_sign)
        bundle["signature_b64"] = b64e(signature)
    return bundle

def hybrid_unwrap_dek(bundle: Dict, recipient_kid: str, sec_key: bytes, kem_alg: str | None = None, aad_str: str | None = None, verifier=None) -> bytes:
    if verifier is not None and "signature_b64" in bundle:
        to_sign = json.dumps({k: bundle[k] for k in bundle if k != "signature_b64"}, separators=(",", ":"), sort_keys=True).encode()
        if not verifier.verify(to_sign, b64d(bundle["signature_b64"])):
            raise ValueError("Signature verification failed")
    aad = (aad_str if aad_str is not None else bundle.get("aad", "")).encode()
    if kem_alg is None:
        kem_alg = bundle.get("kem_alg", "ml-kem-768")
    rec = next((r for r in bundle["recipients"] if r.get("kid") == recipient_kid), None)
    if not rec:
        raise KeyError(f"Recipient kid '{recipient_kid}' not found")
    shared = kem_decapsulate(b64d(rec["kem_ciphertext_b64"]), sec_key, kem_alg)
    info = b"foritech-mlkem-wrap" + aad
    kek = hkdf(salt=b"", ikm=shared, info=info, length=32)
    nonce = b64d(rec["nonce_b64"]); tag = b64d(rec["tag_b64"]); enc_dek = b64d(rec["enc_dek_b64"])
    c = AES.new(kek, AES.MODE_GCM, nonce=nonce); c.update(aad)
    dek = c.decrypt_and_verify(enc_dek, tag)
    if len(dek) != 32:
        raise ValueError("Invalid DEK length")
    return dek
