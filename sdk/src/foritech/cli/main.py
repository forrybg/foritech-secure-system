from __future__ import annotations
import argparse
from ..api import wrap_file, unwrap_file, detect_metadata
from ..models import WrapParams, KemPolicy, RawKemRecipient, X509Recipient
from ..errors import ForitechError

def _parse_recipient(r: str):
    if r.startswith("raw:"): return RawKemRecipient(public_key_path=r[4:])
    if r.startswith("x509:"): return X509Recipient(pem_path=r[5:])
    raise ForitechError(f"Unknown recipient: {r}")

def cmd_wrap(args):
    res = wrap_file(args.input, args.output, [_parse_recipient(r) for r in args.recipient],
                    WrapParams(kid=args.kid, aad=(args.aad.encode() if args.aad else None),
                               kem_policy=KemPolicy([args.kem] if args.kem else ["Kyber768"])))
    print(f"OK: kid={res.kid} nonce={res.nonce} AAD={res.aad_present} KEM={res.kem}")

def cmd_unwrap(args):
    res = unwrap_file(args.input, args.output, None)
    print(f"OK: kid={res.recovered_kid} AAD={res.aad_present} KEM={res.kem}")

def cmd_meta(args):
    meta = detect_metadata(args.input)
    print(f"META: kid={meta.kid} nonce={meta.nonce} AAD={meta.aad_present} KEM={meta.kem}")

def build_parser():
    p = argparse.ArgumentParser(prog="foritech", description="Foritech CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("wrap", help="Wrap (encrypt) file")
    w.add_argument("--in", dest="input", required=True)
    w.add_argument("--out", dest="output", required=True)
    w.add_argument("--recipient", action="append", required=True)
    w.add_argument("--kid")
    w.add_argument("--aad")
    w.add_argument("--kem")
    w.set_defaults(func=cmd_wrap)

    u = sub.add_parser("unwrap", help="Unwrap (decrypt) file")
    u.add_argument("--in", dest="input", required=True)
    u.add_argument("--out", dest="output", required=True)
    u.set_defaults(func=cmd_unwrap)

    m = sub.add_parser("meta", help="Show metadata")
    m.add_argument("--in", dest="input", required=True)
    m.set_defaults(func=cmd_meta)

    return p

def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        args.func(args)
    except ForitechError as e:
        print(f"ERROR: {e}")
        raise SystemExit(2)
    except Exception as e:
        print(f"UNEXPECTED: {e}")
        raise SystemExit(1)
