from __future__ import annotations
import argparse, os, sys
from pathlib import Path

from foritech.api import (
    wrap_file, unwrap_file, detect_metadata,
    wrap_stream as api_wrap_stream, unwrap_stream as api_unwrap_stream,
)
from foritech.errors import ForitechError
from foritech.models import WrapParams, UnwrapParams, RawKemRecipient, Recipient

DEFAULT_STREAM_THRESHOLD_MIB = 64  # 64 MiB

def parse_recipient(s: str) -> Recipient:
    if s.startswith("raw:"):
        return RawKemRecipient(s.split(":",1)[1])
    raise SystemExit(f"Unsupported recipient syntax: {s}")

def cmd_wrap(args: argparse.Namespace) -> int:
    inp = Path(args.input); outp = Path(args.output)
    recipients = [parse_recipient(r) for r in args.recipient]
    aad = args.aad.encode("utf-8") if args.aad is not None else None
    params = WrapParams(kid=args.kid, aad=aad)

    # decide streaming
    threshold_bytes = int(args.stream_threshold_mib) * 1024 * 1024
    size = inp.stat().st_size
    use_stream = args.stream or (not args.no_stream and size >= threshold_bytes)

    try:
        if use_stream:
            with inp.open("rb") as r, outp.open("wb") as w:
                meta = api_wrap_stream(r, w, recipients, params)
                print(f"OK: kid={meta.kid} nonce={meta.nonce} AAD={meta.aad_present} KEM={meta.kem} STREAM=True")
        else:
            meta = wrap_file(inp, outp, recipients, params)
            print(f"OK: kid={meta.kid} nonce={meta.nonce} AAD={meta.aad_present} KEM={meta.kem}")
        return 0
    except ForitechError as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    except Exception as e:
        print(f"UNEXPECTED: {e}", file=sys.stderr); return 1

def cmd_meta(args: argparse.Namespace) -> int:
    try:
        meta = detect_metadata(Path(args.input))
        print(f"META: kid={meta.kid} nonce={meta.nonce} AAD={meta.aad_present} KEM={meta.kem}")
        return 0
    except ForitechError as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    except Exception as e:
        print(f"UNEXPECTED: {e}", file=sys.stderr); return 1

def cmd_unwrap(args: argparse.Namespace) -> int:
    inp = Path(args.input); outp = Path(args.output)
    params = UnwrapParams()

    try:
        if args.stream:
            # force streaming
            with inp.open("rb") as r, outp.open("wb") as w:
                meta = api_unwrap_stream(r, w, params)
                print(f"OK: kid={meta.recovered_kid} AAD={meta.aad_present} KEM={meta.kem} STREAM=True")
                return 0
        # try streaming first; if not a streaming container -> fall back
        try:
            with inp.open("rb") as r, outp.open("wb") as w:
                meta = api_unwrap_stream(r, w, params)
                print(f"OK: kid={meta.recovered_kid} AAD={meta.aad_present} KEM={meta.kem} STREAM=True")
                return 0
        except Exception as e:
            if "Not a streaming container" not in str(e):
                raise
            # fallback to file-mode
            meta = unwrap_file(inp, outp, params)
            print(f"OK: kid={meta.recovered_kid} AAD={meta.aad_present} KEM={meta.kem}")
            return 0
    except ForitechError as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    except Exception as e:
        print(f"UNEXPECTED: {e}", file=sys.stderr); return 1

def main() -> int:
    p = argparse.ArgumentParser(prog="foritech", description="Foritech CLI")
    sp = p.add_subparsers(dest="cmd", required=True)

    pw = sp.add_parser("wrap", help="Wrap (encrypt) file")
    pw.add_argument("--in",  dest="input",  required=True)
    pw.add_argument("--out", dest="output", required=True)
    pw.add_argument("--recipient", action="append", required=True, help="e.g. raw:/path/to/kyber768_pub.bin (can be repeated)")
    pw.add_argument("--kid", required=True)
    pw.add_argument("--aad", required=False)
    # streaming flags
    pw.add_argument("--stream", action="store_true", help="force streaming")
    pw.add_argument("--no-stream", action="store_true", help="force non-streaming")
    pw.add_argument("--stream-threshold-mib", type=int, default=DEFAULT_STREAM_THRESHOLD_MIB,
                    help=f"auto-enable streaming when input >= this size (MiB), default {DEFAULT_STREAM_THRESHOLD_MIB}")

    pu = sp.add_parser("unwrap", help="Unwrap (decrypt) file")
    pu.add_argument("--in",  dest="input",  required=True)
    pu.add_argument("--out", dest="output", required=True)
    pu.add_argument("--stream", action="store_true", help="force streaming (if container is streaming)")

    pm = sp.add_parser("meta", help="Show metadata")
    pm.add_argument("--in", dest="input", required=True)

    args = p.parse_args()
    if args.cmd == "wrap": return cmd_wrap(args)
    if args.cmd == "unwrap": return cmd_unwrap(args)
    if args.cmd == "meta": return cmd_meta(args)
    p.print_help(); return 1

if __name__ == "__main__":
    raise SystemExit(main())
