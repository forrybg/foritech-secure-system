import argparse
import base64
import binascii
import json
import sys
from pathlib import Path
from typing import Tuple, Optional, List, Iterable

from Crypto.Cipher import AES
from foritech.api import unwrap_dek


def _b64_or_hex(s: str) -> bytes:
    s = s.strip()
    # base64
    try:
        return base64.b64decode(s.encode(), validate=True)
    except Exception:
        pass
    # hex
    try:
        return binascii.unhexlify(s.encode())
    except Exception:
        raise ValueError("value is neither base64 nor hex")


def _maybe(obj: dict, *keys: str) -> Optional[str]:
    for k in keys:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _read_enc_any(path: Path) -> Tuple[Optional[bytes], bytes, bytes]:
    """
    Връща (nonce_or_None, ct_or_data, tag_or_empty) от различни формати:
      1) JSON (ключове: nonce/iv/n, ciphertext/ct/enc/payload, tag/mac/auth_tag; b64/hex)
      2) 3 реда base64/hex: nonce\nciphertext\ntag
      3) бинарен dump: може да е nonce(12|16)|ciphertext|tag(16) или само ciphertext|tag → връщаме None за nonce и ще сплитнем после
    """
    data = path.read_bytes()

    # 1) JSON
    try:
        obj = json.loads(data.decode("utf-8"))
        n_s = _maybe(obj, "nonce", "iv", "n", "nonce_b64", "iv_b64")
        c_s = _maybe(obj, "ciphertext", "ct", "enc", "payload")
        t_s = _maybe(obj, "tag", "mac", "auth_tag")
        if c_s and t_s:
            ct = _b64_or_hex(c_s)
            tag = _b64_or_hex(t_s)
            nonce = _b64_or_hex(n_s) if n_s else None
            return nonce, ct, tag
    except Exception:
        pass

    # 2) 3 реда base64/hex
    try:
        parts = data.decode("utf-8").strip().splitlines()
        if len(parts) == 3:
            n = _b64_or_hex(parts[0])
            c = _b64_or_hex(parts[1])
            t = _b64_or_hex(parts[2])
            return n, c, t
    except Exception:
        pass

    # 3) бинарен — не знаем дали има nonce; връщаме None и сплитваме по-късно
    if len(data) < 16:
        raise SystemExit(f"encrypted file too short: {len(data)} bytes")
    return None, data, b""


def _kids_in_bundle(bundle: dict) -> List[str]:
    kids: List[str] = []
    for r in bundle.get("recipients", []):
        if isinstance(r, dict):
            h = r.get("header") or {}
            k = None
            if isinstance(h, dict) and h.get("kid"): k = str(h["kid"])
            if not k and r.get("kid"): k = str(r["kid"])
            if k and k not in kids: kids.append(k)
    for sect in ("header", "protected"):
        h = bundle.get(sect)
        if isinstance(h, dict) and h.get("kid"):
            k = str(h["kid"])
            if k not in kids: kids.append(k)
    return kids


def _pick_alg(bundle: dict) -> Optional[str]:
    for k in ("kem_alg", "kem", "alg", "algorithm"):
        v = bundle.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _nonce_candidates(bundle: dict, from_file_nonce: Optional[bytes], binary_ct: Optional[bytes]) -> Iterable[bytes]:
    """
    Възможни nonce варианти:
      - този от файла (ако е наличен)
      - от bundle (nonce/iv/n; b64/hex; в root/protected/header)
      - ако файлът е бинарен dump (ct=data без tag): пробвай split с 12 и 16 байта nonce
    """
    yielded = set()

    if from_file_nonce:
        yielded.add(from_file_nonce)
        yield from_file_nonce

    def _push_str(n_opt: Optional[str]):
        if n_opt:
            try:
                b = _b64_or_hex(n_opt)
                if b not in yielded:
                    yielded.add(b)
                    yield b
            except Exception:
                pass

    for k in ("nonce", "iv", "n", "nonce_b64", "iv_b64"):
        yield from _push_str(_maybe(bundle, k)) or ()
    for sect in ("protected", "header"):
        h = bundle.get(sect)
        if isinstance(h, dict):
            for k in ("nonce", "iv", "n", "nonce_b64", "iv_b64"):
                v = h.get(k)
                if isinstance(v, str):
                    yield from _push_str(v) or ()

    if binary_ct is not None:
        data = binary_ct
        for nlen in (12, 16):
            if len(data) >= nlen + 16:
                nonce = data[:nlen]
                if nonce not in yielded:
                    yielded.add(nonce)
                    yield nonce


def _split_binary_with_nonce_tag(data: bytes, nonce: bytes) -> Tuple[bytes, bytes]:
    if len(data) < len(nonce) + 16:
        raise ValueError("binary enc too short for chosen nonce length")
    ct = data[len(nonce):-16]
    tag = data[-16:]
    return ct, tag


def _aad_candidates(bundle: dict, cli_aad: str) -> List[Optional[bytes]]:
    cands: List[Optional[bytes]] = [cli_aad.encode()]
    v = bundle.get("aad")
    if isinstance(v, str):
        b = v.encode()
        if b not in cands: cands.append(b)
    for sect in ("protected", "header"):
        h = bundle.get(sect)
        if isinstance(h, dict) and isinstance(h.get("aad"), str):
            b = h["aad"].encode()
            if b not in cands: cands.append(b)
    if None not in cands: cands.append(None)
    return cands


def main():
    ap = argparse.ArgumentParser(description="Unwrap and decrypt file with AES-GCM using foritech bundle")
    ap.add_argument("enc_file", type=Path, help="encrypted file (JSON/3-line base64/hex or binary nonce|ct|tag or ct|tag)")
    ap.add_argument("bundle_json", type=Path, help="bundle json path")
    ap.add_argument("out_file", type=Path, help="output plaintext path")
    ap.add_argument("aad", help="AAD string")
    ap.add_argument("kid", nargs="?", default=None, help="recipient key id (optional)")
    ap.add_argument("sec_path", type=Path, help="private key file for recipient (.kem.sec)")
    args = ap.parse_args()

    # bundle
    try:
        bundle = json.loads(args.bundle_json.read_text(encoding="utf-8"))
    except Exception:
        print("ERROR: bundle must be JSON file", file=sys.stderr)
        sys.exit(2)

    # candidate kids
    cand_kids: List[str] = ([args.kid] if args.kid else []) + [k for k in _kids_in_bundle(bundle) if k != args.kid]
    if not cand_kids:
        print("ERROR: no kid provided and none found in bundle", file=sys.stderr)
        sys.exit(2)

    alg = _pick_alg(bundle)

    # unwrap (пробвай всеки kid)
    dek = None
    used_kid = None
    last = None
    for k in cand_kids:
        try:
            dek = unwrap_dek(bundle, kid=k, sec_bytes=args.sec_path.read_bytes(), aad=args.aad, alg=alg)
            used_kid = k
            break
        except Exception as e:
            last = e
    if dek is None:
        print(f"ERROR: unwrap_dek failed for candidates {cand_kids}: {last}", file=sys.stderr)
        sys.exit(3)

    # прочети enc
    file_nonce, file_ct_or_data, file_tag = _read_enc_any(args.enc_file)

    # списък от възможни nonce и AAD
    nonce_list = list(_nonce_candidates(bundle, file_nonce, file_ct_or_data if file_tag == b"" else None))
    aad_list = _aad_candidates(bundle, args.aad)

    # пробвай всички комбинации
    for nonce in nonce_list:
        ct, tag = (file_ct_or_data, file_tag)
        if tag == b"":  # целият dump → раздели спрямо nonce
            try:
                ct, tag = _split_binary_with_nonce_tag(file_ct_or_data, nonce)
            except Exception:
                continue
        for aad_b in aad_list:
            try:
                c = AES.new(dek, AES.MODE_GCM, nonce=nonce)
                if aad_b is not None:
                    c.update(aad_b)
                pt = c.decrypt_and_verify(ct, tag)
                args.out_file.write_bytes(pt)
                which_aad = "CLI AAD" if aad_b == args.aad.encode() else ("bundle AAD" if aad_b is not None else "no AAD")
                which_nonce = f"{len(nonce)}B"
                print(f"OK: kid={used_kid}, nonce={which_nonce}, AAD={which_aad} -> {args.out_file}")
                return
            except Exception:
                continue

    print("ERROR: AES-GCM decrypt failed with all nonce/AAD variants", file=sys.stderr)
    sys.exit(4)


if __name__ == "__main__":
    main()
