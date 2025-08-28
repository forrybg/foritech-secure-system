from __future__ import annotations
import argparse
import json
from pathlib import Path
from ..crypto.pqc_kem import kem_generate, b64e, normalize_alg

def _cmd_kem_genkey(args) -> int:
    alg = normalize_alg(args.kem)
    pub, sec = kem_generate(alg)
    out = Path(args.out)
    # секрета в <out>.kem.sec (raw bytes), публичния в <out>.kem.pub.json
    Path(f"{out}.kem.sec").write_bytes(sec)
    Path(f"{out}.kem.pub.json").write_text(
        json.dumps({"kid": out.name, "pub_b64": b64e(pub)}, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote: {out}.kem.sec and {out}.kem.pub.json")
    return 0

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="foritech.cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("kem-genkey", help="Generate KEM keypair")
    g.add_argument("-k", "--kem", required=True, help="Algorithm, e.g. Kyber768 or ML-KEM-768")
    g.add_argument("-o", "--out", required=True, help="Output prefix (no extension)")
    g.set_defaults(func=_cmd_kem_genkey)

    args = p.parse_args(argv)
    return args.func(args)
