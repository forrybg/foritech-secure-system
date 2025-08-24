from pathlib import Path
import os, json
from Crypto.Cipher import AES
from foritech.api import recipients_from_files, wrap_existing_dek_for

def aes_gcm_encrypt(key: bytes, data: bytes, aad: bytes=b""):
    nonce = os.urandom(12)
    c = AES.new(key, AES.MODE_GCM, nonce=nonce)
    c.update(aad)
    enc, tag = c.encrypt_and_digest(data)
    return nonce, enc, tag

def main(in_path: str, out_enc: str, out_bundle: str, aad: str, *pubjsons: str):
    data = Path(in_path).read_bytes()
    dek = os.urandom(32)  # 256-bit
    recips = recipients_from_files(list(pubjsons))

    # Стабилни KID-ове (за демо/тестове), ако липсват
    defaults = ["ops-1", "dr-1", "r3", "r4", "r5"]
    for i, r in enumerate(recips):
        if not r.get("kid"):
            r["kid"] = defaults[i] if i < len(defaults) else f"r{i+1}"

    bundle = wrap_existing_dek_for(dek, recips, aad=aad, alg="ml-kem-768")

    nonce, enc, tag = aes_gcm_encrypt(dek, data, aad=aad.encode())
    Path(out_enc).write_bytes(nonce + tag + enc)
    Path(out_bundle).write_text(json.dumps(bundle, separators=(",", ":"), sort_keys=True))
    print(f"Encrypted → {out_enc}  |  Bundle → {out_bundle}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 6:
        print("usage: wrap_file.py <in> <out.enc> <out.bundle.json> <aad> <recip1.pub.json> [recip2.pub.json ...]")
        raise SystemExit(2)
    main(*sys.argv[1:5], *sys.argv[5:])
