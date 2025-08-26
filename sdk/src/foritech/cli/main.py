from __future__ import annotations
import argparse
from pathlib import Path

from foritech.api import (
    wrap_file, unwrap_file, wrap_stream, unwrap_stream, detect_metadata
)
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams


def _build_recipients(recipient_args: list[str]):
    recips = []
    for r in recipient_args:
        if r.startswith("raw:"):
            recips.append(RawKemRecipient(r.split("raw:", 1)[1]))
        else:
            raise ValueError(f"Unsupported recipient: {r}")
    return recips


def _print_meta(prefix: str, meta) -> None:
    out = f"{prefix}: kid={meta.kid} nonce={meta.nonce} AAD={meta.aad_present} KEM={meta.kem}"
    if hasattr(meta, "stream"):
        out += f" STREAM={getattr(meta, 'stream', False)}"
        if getattr(meta, "stream", False) and getattr(meta, "chunk_size", None):
            out += f" CHUNK={meta.chunk_size}"
    print(out)


def cmd_wrap(args: argparse.Namespace) -> int:
    try:
        in_p, out_p = Path(args.input), Path(args.output)
        recips = _build_recipients(args.recipient)
        params = WrapParams(kid=args.kid, aad=args.aad.encode("utf-8") if args.aad else None)

        size = in_p.stat().st_size if in_p.exists() else 0
        thr_mib = int(args.stream_threshold_mib or 64)
        threshold = thr_mib * 1024 * 1024
        force_stream = bool(args.stream)
        force_no_stream = bool(args.no_stream)
        do_stream = force_stream or (not force_no_stream and size >= threshold)

        if do_stream:
            with in_p.open("rb") as r, out_p.open("wb") as w:
                wrap_stream(r, w, recips, params)
        else:
            wrap_file(in_p, out_p, recips, params)

        meta = detect_metadata(out_p)
        _print_meta("OK", meta)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def cmd_meta(args: argparse.Namespace) -> int:
    try:
        meta = detect_metadata(Path(args.input))
        _print_meta("META", meta)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def cmd_unwrap(args: argparse.Namespace) -> int:
    try:
        in_p, out_p = Path(args.input), Path(args.output)
        meta = detect_metadata(in_p)
        # ако контейнерът е stream → ползваме stream разпаковането
        if getattr(meta, "stream", False):
            with in_p.open("rb") as r, out_p.open("wb") as w:
                unwrap_stream(r, w, UnwrapParams())
        else:
            unwrap_file(in_p, out_p, UnwrapParams())
        # покажи реалния meta (след wrap/unwrap консистентен)
        meta2 = detect_metadata(in_p)
        _print_meta("OK", meta2)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="foritech", description="Foritech CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_wrap = sub.add_parser("wrap", help="Wrap (encrypt) file")
    p_wrap.add_argument("--in", dest="input", required=True)
    p_wrap.add_argument("--out", dest="output", required=True)
    p_wrap.add_argument("--recipient", action="append", required=True, help="e.g. raw:/path/to/kyber768_pub.bin")
    p_wrap.add_argument("--kid", default=None)
    p_wrap.add_argument("--aad", default=None)
    p_wrap.add_argument("--stream", action="store_true", help="Force streaming mode")
    p_wrap.add_argument("--no-stream", action="store_true", help="Force non-stream mode (in-memory)")
    p_wrap.add_argument("--stream-threshold-mib", type=int, default=64, help="Auto streaming threshold MiB")
    p_wrap.set_defaults(func=cmd_wrap)

    p_unwrap = sub.add_parser("unwrap", help="Unwrap (decrypt) file")
    p_unwrap.add_argument("--in", dest="input", required=True)
    p_unwrap.add_argument("--out", dest="output", required=True)
    p_unwrap.set_defaults(func=cmd_unwrap)

    p_meta = sub.add_parser("meta", help="Show metadata")
    p_meta.add_argument("--in", dest="input", required=True)
    p_meta.set_defaults(func=cmd_meta)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
