from __future__ import annotations
import argparse
import json
from pathlib import Path

from foritech.api import (
    wrap_file, unwrap_file, wrap_stream, unwrap_stream, detect_metadata
)
from foritech.models import RawKemRecipient, WrapParams, UnwrapParams
from foritech.pki.x509_tools import (
    extract_hybrid_info, extract_pqc_pub,
    generate_hybrid_selfsigned, generate_ca_selfsigned, issue_leaf_cert,
)

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
        if getattr(meta, "stream", False):
            with in_p.open("rb") as r, out_p.open("wb") as w:
                unwrap_stream(r, w, UnwrapParams())
        else:
            unwrap_file(in_p, out_p, UnwrapParams())
        meta2 = detect_metadata(in_p)
        _print_meta("OK", meta2)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def cmd_x509_info(args: argparse.Namespace) -> int:
    try:
        data = Path(args.input).read_bytes()
        info = extract_hybrid_info(data)
        if args.json:
            print(json.dumps(info or {}, separators=(",", ":"), ensure_ascii=False))
        else:
            if not info:
                print("X509: no FORITECH_HYBRID extension")
            else:
                kem = info.get("kem"); fmt = info.get("format")
                b64 = info.get("pqc_pub_b64") or info.get("spki_b64") or ""
                print(f"X509: kem={kem} format={fmt} pqc_pub_b64_len={len(b64)} v={info.get('v')}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def cmd_x509_make(args: argparse.Namespace) -> int:
    try:
        pqc_pub = Path(args.pqc_pub).read_bytes()
        cert_pem, key_pem = generate_hybrid_selfsigned(
            cn=args.cn, kem_name=args.kem, pqc_pubkey_bytes=pqc_pub,
            days_valid=args.days, ext_format=("spki" if args.format == "spki" else "raw")
        )
        Path(args.cert_out).write_bytes(cert_pem)
        Path(args.key_out).write_bytes(key_pem)
        if args.chain_out:
            Path(args.chain_out).write_bytes(cert_pem)
        info = extract_hybrid_info(cert_pem)
        if info:
            print(f"X509: kem={info.get('kem')} format={info.get('format')} v={info.get('v')}")
        print(f"Written: cert={args.cert_out} key={args.key_out}" + (f" chain={args.chain_out}" if args.chain_out else ""))
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def cmd_x509_make_ca(args: argparse.Namespace) -> int:
    try:
        cert_pem, key_pem = generate_ca_selfsigned(args.cn, days_valid=args.days)
        Path(args.cert_out).write_bytes(cert_pem)
        Path(args.key_out).write_bytes(key_pem)
        print(f"CA written: cert={args.cert_out} key={args.key_out}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def cmd_x509_issue(args: argparse.Namespace) -> int:
    try:
        ca_cert = Path(args.ca_cert).read_bytes()
        ca_key  = Path(args.ca_key).read_bytes()
        pqc_pub = Path(args.pqc_pub).read_bytes()
        leaf = issue_leaf_cert(
            ca_cert_pem=ca_cert, ca_key_pem=ca_key,
            subject_cn=args.cn, kem_name=args.kem,
            pqc_pubkey_bytes=pqc_pub, days_valid=args.days,
            ext_format=("spki" if args.format == "spki" else "raw")
        )
        Path(args.cert_out).write_bytes(leaf)
        if args.chain_out:
            Path(args.chain_out).write_bytes(leaf + b"\n" + ca_cert)
        info = extract_hybrid_info(leaf)
        if info:
            print(f"X509: kem={info.get('kem')} format={info.get('format')} v={info.get('v')}")
        print(f"Leaf written: cert={args.cert_out}" + (f" chain={args.chain_out}" if args.chain_out else ""))
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def cmd_x509_extract_pqc(args: argparse.Namespace) -> int:
    try:
        cert = Path(args.input).read_bytes()
        kem, pub = extract_pqc_pub(cert)
        Path(args.out).write_bytes(pub)
        print(f"PQC pub extracted: kem={kem} bytes={len(pub)} -> {args.out}")
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

    p_xinfo = sub.add_parser("x509-info", help="Show Foritech hybrid info from X.509 cert")
    p_xinfo.add_argument("--in", dest="input", required=True)
    p_xinfo.add_argument("--json", action="store_true", help="Output JSON payload")
    p_xinfo.set_defaults(func=cmd_x509_info)

    p_xmake = sub.add_parser("x509-make", help="Generate hybrid self-signed cert with PQC extension")
    p_xmake.add_argument("--cn", required=True, help="Common Name")
    p_xmake.add_argument("--kem", default="Kyber768")
    p_xmake.add_argument("--pqc-pub", required=True, help="Path to PQC public key (raw)")
    p_xmake.add_argument("--cert-out", default="hybrid_cert.pem")
    p_xmake.add_argument("--key-out", default="hybrid_key.pem")
    p_xmake.add_argument("--days", type=int, default=365)
    p_xmake.add_argument("--format", choices=["raw","spki"], default="raw", help="Extension key encoding")
    p_xmake.add_argument("--chain-out", default=None, help="Write fullchain file (self cert)")
    p_xmake.set_defaults(func=cmd_x509_make)

    p_xmake_ca = sub.add_parser("x509-make-ca", help="Generate self-signed CA (ECDSA P-256)")
    p_xmake_ca.add_argument("--cn", required=True)
    p_xmake_ca.add_argument("--cert-out", default="ca_cert.pem")
    p_xmake_ca.add_argument("--key-out",  default="ca_key.pem")
    p_xmake_ca.add_argument("--days", type=int, default=3650)
    p_xmake_ca.set_defaults(func=cmd_x509_make_ca)

    p_xissue = sub.add_parser("x509-issue", help="Issue leaf cert signed by CA, embedding PQC extension")
    p_xissue.add_argument("--cn", required=True)
    p_xissue.add_argument("--kem", default="Kyber768")
    p_xissue.add_argument("--pqc-pub", required=True)
    p_xissue.add_argument("--ca-cert", required=True)
    p_xissue.add_argument("--ca-key",  required=True)
    p_xissue.add_argument("--cert-out", default="leaf_cert.pem")
    p_xissue.add_argument("--days", type=int, default=825)
    p_xissue.add_argument("--format", choices=["raw","spki"], default="raw", help="Extension key encoding")
    p_xissue.add_argument("--chain-out", default=None, help="Write fullchain file (leaf + CA)")
    p_xissue.set_defaults(func=cmd_x509_issue)

    p_xextract = sub.add_parser("x509-extract-pqc", help="Extract PQC public key bytes from hybrid X.509")
    p_xextract.add_argument("--in", dest="input", required=True)
    p_xextract.add_argument("--out", dest="out", required=True)
    p_xextract.set_defaults(func=cmd_x509_extract_pqc)
    try:
        augment_with_keys_and_verify(ap)
    except Exception:
        pass

    args = ap.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())


# === auto-appended: keys + x509-verify ===
def augment_with_keys_and_verify(p):
    sub = None
    for line in p._positionals._actions:  # type: ignore[attr-defined]
        pass
    sub = p._subparsers._group_actions[0]  # type: ignore[attr-defined]

    def cmd_x509_verify(a):
        from pathlib import Path
        from ..x509_utils import verify_chain
        leaf = Path(a.leaf).read_bytes()
        chain = Path(a.chain).read_bytes() if a.chain else None
        root = Path(a.root).read_bytes() if a.root else None
        try:
            res = verify_chain(leaf, chain, root, check_time=True)
            print(f"CHAIN OK depth={res['depth']}")
            for s in res["subjects"]:
                print(" -", s)
            return 0
        except Exception as e:
            print("VERIFY ERROR:", e)
            return 2

    xv = sub.add_parser("x509-verify", help="Verify leaf + optional chain + optional root")
    xv.add_argument("--leaf", required=True)
    xv.add_argument("--chain", default=None)
    xv.add_argument("--root", default=None)
    xv.set_defaults(func=cmd_x509_verify)

    def cmd_keygen(a):
        from ..key_utils import keygen_kyber
        info = keygen_kyber(a.kid, a.out_dir)
        print(f"Key generated: kid={info['kid']} kem={info['kem']}")
        print(f"  pub: {info['pub']}")
        print(f"  sec: {info['sec']}")
        print("Tip: export FORITECH_SK to your secret key for unwrap auto-detect.")
        return 0

    kg = sub.add_parser("keygen", help="Generate Kyber768 keypair")
    kg.add_argument("--kid", default=None)
    kg.add_argument("--out-dir", default=None)
    kg.set_defaults(func=cmd_keygen)

    def cmd_key_list(a):
        from ..key_utils import list_keys
        lst = list_keys(a.dir)
        if not lst:
            print("No keys found.")
            return 1
        for e in lst:
            print(f"{e['kid']:>18}  kem={e['kem']}  pub={'yes' if e['pub'] else 'no '}  sec={'yes' if e['sec'] else 'no '}")
        return 0

    kl = sub.add_parser("key-list", help="List Kyber keys")
    kl.add_argument("--dir", default=None)
    kl.set_defaults(func=cmd_key_list)

    def cmd_key_show(a):
        from ..key_utils import show_key
        info = show_key(kid=a.kid, path=a.path)
        print(f"{info['path']}  kind={info['kind']} kem={info['kem']} size={info['size']}")
        return 0

    ks = sub.add_parser("key-show", help="Show key info by --kid or --path")
    g = ks.add_mutually_exclusive_group(required=True)
    g.add_argument("--kid", default=None)
    g.add_argument("--path", default=None)
    ks.set_defaults(func=cmd_key_show)
