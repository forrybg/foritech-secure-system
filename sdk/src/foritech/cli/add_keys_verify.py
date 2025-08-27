from __future__ import annotations
import argparse
from pathlib import Path
from ..key_utils import keygen_kyber, list_keys, show_key
from ..x509_utils import verify_chain

def _get_subparsers(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            return act
    return parser.add_subparsers(dest="cmd")

def inject(parser: argparse.ArgumentParser) -> None:
    sub = _get_subparsers(parser)

    # x509-verify
    def cmd_x509_verify(a):
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
    p = sub.add_parser("x509-verify", help="Verify leaf + optional chain + optional root (offline)")
    p.add_argument("--leaf", required=True)
    p.add_argument("--chain", default=None)
    p.add_argument("--root", default=None)
    p.set_defaults(func=cmd_x509_verify)

    # keygen
    def cmd_keygen(a):
        info = keygen_kyber(a.kid, a.out_dir)
        print(f"Key generated: kid={info['kid']} kem={info['kem']}")
        print(f"  pub: {info['pub']}")
        print(f"  sec: {info['sec']}")
        print("Tip: export FORITECH_SK to your secret key for unwrap auto-detect.")
        return 0
    p = sub.add_parser("keygen", help="Generate Kyber768 keypair")
    p.add_argument("--kid", default=None)
    p.add_argument("--out-dir", default=None)
    p.set_defaults(func=cmd_keygen)

    # key-list
    def cmd_key_list(a):
        lst = list_keys(a.dir)
        if not lst:
            print("No keys found.")
            return 1
        for e in lst:
            print(f"{e['kid']:>18}  kem={e['kem']}  pub={'yes' if e['pub'] else 'no '}  sec={'yes' if e['sec'] else 'no '}")
        return 0
    p = sub.add_parser("key-list", help="List Kyber keys")
    p.add_argument("--dir", default=None)
    p.set_defaults(func=cmd_key_list)

    # key-show
    def cmd_key_show(a):
        info = show_key(kid=a.kid, path=a.path)
        print(f"{info['path']}  kind={info['kind']} kem={info['kem']} size={info['size']}")
        return 0
    p = sub.add_parser("key-show", help="Show key info by --kid or --path")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--kid", default=None)
    g.add_argument("--path", default=None)
    p.set_defaults(func=cmd_key_show)
