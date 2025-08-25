import argparse, json, base64, os, sys
from pathlib import Path
from typing import List
from Crypto.Cipher import AES

from foritech.api import (
    recipients_from_files,
    wrap_existing_dek_for,
)

def b64(x: bytes) -> str:
    return base64.b64encode(x).decode()

def main():
    ap = argparse.ArgumentParser(description="Encrypt file and produce bundle for recipients (AES-256-GCM + KEM)")
    ap.add_argument("in_file", type=Path, help="plaintext file to encrypt")
    ap.add_argument("out_enc", type=Path, help="output encrypted file (JSON with nonce/ciphertext/tag in base64)")
    ap.add_argument("out_bundle", type=Path, help="output bundle json (wrap of DEK for recipients)")
    ap.add_argument("aad", help="AAD string")
    ap.add_argument("pubkeys", nargs="+", type=Path, help="one or more *.kem.pub.json files (recipients)")
    args = ap.parse_args()

    # 1) съберем получателите
    recips = recipients_from_files([str(p) for p in args.pubkeys])

    # 2) DEK + wrap към всички получатели (alg от env или kyber768 по подразбиране)
    alg = os.environ.get("FORITECH_TEST_KEM", "kyber768")
    dek = os.urandom(32)  # 256-bit
    bundle = wrap_existing_dek_for(dek, recips, aad=args.aad, alg=alg)

    # 3) локално шифриране на файла с DEK (AES-256-GCM)
    pt = args.in_file.read_bytes()
    nonce = os.urandom(12)
    c = AES.new(dek, AES.MODE_GCM, nonce=nonce)
    c.update(args.aad.encode())
    ct, tag = c.encrypt_and_digest(pt)

    # 4) запис
    args.out_enc.write_text(json.dumps({
        "nonce": b64(nonce),
        "ciphertext": b64(ct),
        "tag": b64(tag),
    }), encoding="utf-8")
    args.out_bundle.write_text(json.dumps(bundle), encoding="utf-8")

    print(f"Wrote ENC → {args.out_enc}  |  BUNDLE → {args.out_bundle}  |  recipients={len(recips)}  alg={bundle.get('kem_alg')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
