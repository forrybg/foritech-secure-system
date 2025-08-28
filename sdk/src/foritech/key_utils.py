from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional, List, Dict
try:
    import oqs  # liboqs-python
except Exception:  # pragma: no cover
    oqs = None

KEM_NAME = "Kyber768"

def keys_dir() -> Path:
    return Path(os.environ.get("FORITECH_KEYS", str(Path.home() / ".foritech" / "keys"))).expanduser()

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def keygen_kyber(kid: Optional[str] = None, out_dir: Optional[str|Path] = None) -> Dict[str, str]:
    if oqs is None:
        raise RuntimeError("liboqs-python (module 'oqs') is missing. Run scripts/dev_install_oqs.sh")
    d = keys_dir() if out_dir is None else Path(out_dir)
    _ensure_dir(d)
    if not kid:
        kid = f"kyber-{int(time.time())}"
    with oqs.KeyEncapsulation(KEM_NAME) as kem:
        pub = kem.generate_keypair()
        try:
            sec = kem.export_secret_key()
        except Exception:
            sec = getattr(kem, "secret_key", None)
            if sec is None:
                raise
    pub_path = d / f"{kid}_pub.bin"
    sec_path = d / f"{kid}_sec.bin"
    pub_path.write_bytes(pub)
    sec_path.write_bytes(sec)
    try: os.chmod(sec_path, 0o600)
    except Exception: pass
    return {"kid": kid, "kem": KEM_NAME, "pub": str(pub_path), "sec": str(sec_path)}

def list_keys(dir_path: Optional[str|Path] = None) -> List[Dict[str, str]]:
    d = keys_dir() if dir_path is None else Path(dir_path)
    out: List[Dict[str, str]] = []
    if not d.exists(): return out
    pubs = {p.stem[:-4]: p for p in d.glob("*_pub.bin") if p.is_file()}
    secs = {p.stem[:-4]: p for p in d.glob("*_sec.bin") if p.is_file()}
    for kid, pubp in pubs.items():
        secp = secs.get(kid)
        out.append({"kid": kid, "kem": KEM_NAME, "pub": str(pubp), "sec": str(secp) if secp else ""})
    for kid, secp in secs.items():
        if kid not in pubs:
            out.append({"kid": kid, "kem": KEM_NAME, "pub": "", "sec": str(secp)})
    out.sort(key=lambda x: x["kid"])
    return out

def show_key(kid: Optional[str] = None, path: Optional[str|Path] = None) -> Dict[str, str|int]:
    if not kid and not path:
        raise ValueError("Provide --kid or --path")
    if kid:
        d = keys_dir()
        cand = [d/f"{kid}_pub.bin", d/f"{kid}_sec.bin"]
        for p in cand:
            if p.exists():
                path = p
                break
        if path is None:
            raise FileNotFoundError(f"No key files found for kid={kid} in {d}")
    p = Path(path)  # type: ignore[arg-type]
    data = p.read_bytes()
    kind = "pub" if p.name.endswith("_pub.bin") else ("sec" if p.name.endswith("_sec.bin") else "raw")
    return {"path": str(p), "kind": kind, "kem": KEM_NAME, "size": len(data)}
