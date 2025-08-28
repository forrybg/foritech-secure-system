#!/usr/bin/env python3
import sys
import hashlib
from pathlib import Path
from foritech.api import wrap_stream, unwrap_stream
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def main():
    if len(sys.argv) != 5:
        print("usage: stream_roundtrip.py <in> <enc> <out> <pubkey>", file=sys.stderr)
        sys.exit(2)
    inp, enc, out, pub = map(Path, sys.argv[1:])
    kid = "kid-stream"
    # WRAP (stream)
    with inp.open("rb") as r, enc.open("wb") as w:
        wrap_stream(r, w, [RawKemRecipient(str(pub))], WrapParams(kid=kid, aad=b"stream-demo"))
    # UNWRAP (stream)
    with enc.open("rb") as r, out.open("wb") as w:
        unwrap_stream(r, w, UnwrapParams())
    # verify
    print("SHA256 in :", sha256(inp))
    print("SHA256 out:", sha256(out))
    print("OK" if sha256(inp) == sha256(out) else "MISMATCH!")
if __name__ == "__main__":
    main()
