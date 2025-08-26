#!/usr/bin/env python3
import os, pathlib, sys
try:
    import oqs
except Exception as e:
    print("ERROR: pyoqs (oqs) is required. Try: pip install pyoqs", file=sys.stderr)
    sys.exit(1)

out_dir = pathlib.Path(os.environ.get("FORITECH_KEYDIR", "~/.foritech/keys")).expanduser()
out_dir.mkdir(parents=True, exist_ok=True)
pub = out_dir / "kyber768_pub.bin"
sec = out_dir / "kyber768_sec.bin"

with oqs.KeyEncapsulation("Kyber768") as kem:
    pk = kem.generate_keypair()
    sk = kem.export_secret_key()

pub.write_bytes(pk)
sec.write_bytes(sk)

print(f"Public : {pub}")
print(f"Secret : {sec}")
print("Tip: export FORITECH_SK to point to your secret key, e.g.:")
print(f'  export FORITECH_SK="{sec}"')
