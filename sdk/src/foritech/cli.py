from __future__ import annotations
import argparse, json
from pathlib import Path
from .crypto.pqc_kem import kem_generate, b64e, b64d, kem_encapsulate, kem_decapsulate
from .crypto.hybrid_wrap import hybrid_unwrap_dek, hybrid_wrap_dek

import json

def _extract_kid_from_bundle_bytes(b: bytes):
    """
    Връща kid от JSON bundle, ако може. Търси:
      - recipients[*].header.kid
      - recipients[*].kid
      - header.kid, protected.kid
    Ако не намери -> None.
    """
    try:
        data = json.loads(b.decode("utf-8"))
    except Exception:
        return None
    kids = set()
    rec = data.get("recipients") or []
    for r in rec:
        if isinstance(r, dict):
            h = r.get("header") or {}
            if isinstance(h, dict) and h.get("kid"):
                kids.add(str(h["kid"]))
            if r.get("kid"):
                kids.add(str(r["kid"]))
    for k in ("header", "protected"):
        h = data.get(k)
        if isinstance(h, dict) and h.get("kid"):
            kids.add(str(h["kid"]))
    if len(kids) == 1:
        return next(iter(kids))
    return None


def cmd_kem_genkey(args):
    pub, sec = kem_generate(args.k)
    Path(args.o + ".kem.sec").write_bytes(sec)
    Path(args.o + ".kem.pub.json").write_text(json.dumps({"alg": args.k, "pub_b64": b64e(pub)}, indent=2))
    print(f"Wrote: {args.o}.kem.sec and {args.o}.kem.pub.json")

def cmd_hybrid_wrap(args):
    recips = json.loads(Path(args.recipients).read_text())
    bundle = hybrid_wrap_dek(recips, kem_alg=args.kem, aad_str=args.aad, signer=None)
    Path(args.o).write_text(json.dumps(bundle, separators=(",", ":"), sort_keys=True))
    print(f"Wrote bundle: {args.o}")

def cmd_hybrid_unwrap(args):
    bundle = json.loads(Path(args.bundle).read_text())
    sec = Path(args.secret).read_bytes()
    dek = hybrid_unwrap_dek(bundle, recipient_kid=args.kid, sec_key=sec, kem_alg=args.kem, aad_str=args.aad)
    Path(args.out_dek).write_bytes(dek)
    print(f"Wrote DEK ({len(dek)} bytes) → {args.out_dek}")

def main(argv=None):
    p = argparse.ArgumentParser("foritech")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("kem-genkey")
    s1.add_argument("-k","--k", default="ml-kem-768")
    s1.add_argument("-o","--o", required=True)
    s1.set_defaults(func=cmd_kem_genkey)

    s2 = sub.add_parser("hybrid-wrap")
    s2.add_argument("--recipients", required=True)
    s2.add_argument("--aad", default="")
    s2.add_argument("-o","--o", required=True)
    s2.add_argument("--kem", default="ml-kem-768")
    s2.set_defaults(func=cmd_hybrid_wrap)

    s3 = sub.add_parser("hybrid-unwrap")
    s3.add_argument("--secret", required=True)
    s3.add_argument("--kid", required=True)
    s3.add_argument("--bundle", required=True)
    s3.add_argument("--aad", default="")
    s3.add_argument("--out-dek", required=True)
    s3.add_argument("--kem", default="ml-kem-768")
    s3.set_defaults(func=cmd_hybrid_unwrap)

    args = p.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
