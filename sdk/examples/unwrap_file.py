from pathlib import Path
import json
from Crypto.Cipher import AES
from foritech.api import unwrap_dek

def aes_gcm_decrypt(key: bytes, blob: bytes, aad: bytes=b"") -> bytes:
    nonce, tag, enc = blob[:12], blob[12:28], blob[28:]
    c = AES.new(key, AES.MODE_GCM, nonce=nonce)
    c.update(aad)
    return c.decrypt_and_verify(enc, tag)

def main(in_enc: str, in_bundle: str, out_plain: str, aad: str, kid: str, secret_kem: str):
    bundle = json.loads(Path(in_bundle).read_text())
    sec = Path(secret_kem).read_bytes()
    # опит с подадения kid
    try:
        dek = unwrap_dek(bundle, kid=kid, sec_bytes=sec, aad=aad, alg="ml-kem-768")
    except KeyError:
        # fallback: stem на файла със secret (напр. a.kem.sec -> a.kem)
        alt_kid = Path(secret_kem).stem
        dek = unwrap_dek(bundle, kid=alt_kid, sec_bytes=sec, aad=aad, alg="ml-kem-768")
    plain = aes_gcm_decrypt(dek, Path(in_enc).read_bytes(), aad=aad.encode())
    Path(out_plain).write_bytes(plain)
    print(f"Decrypted → {out_plain}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 7:
        print("usage: unwrap_file.py <in.enc> <in.bundle.json> <out> <aad> <kid> <recipient.kem.sec>")
        raise SystemExit(2)
    main(*sys.argv[1:])
