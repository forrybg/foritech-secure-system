import base64
import oqs
from oqs import KeyEncapsulation

_ENABLED = set(oqs.get_enabled_kem_mechanisms())
_EQUIVS = [("ML-KEM-512","Kyber512"),("ML-KEM-768","Kyber768"),("ML-KEM-1024","Kyber1024")]

_ALIASES = {}
for ml, ky in _EQUIVS:
    for user_in in [ml, ml.lower(), ml.replace("-","").lower(), ky, ky.lower()]:
        if ml in _ENABLED:
            _ALIASES[user_in] = ml
        elif ky in _ENABLED:
            _ALIASES[user_in] = ky

def _norm_alg(alg: str) -> str:
    a = alg.strip(); a_norm = a.upper().replace("_","-")
    if a in _ENABLED: return a
    if a_norm in _ENABLED: return a_norm
    t = _ALIASES.get(a) or _ALIASES.get(a.lower()) or _ALIASES.get(a_norm)
    if t: return t
    for ml, ky in _EQUIVS:
        if "512" in a_norm and (ml in _ENABLED or ky in _ENABLED): return ml if ml in _ENABLED else ky
        if "768" in a_norm and (ml in _ENABLED or ky in _ENABLED): return ml if ml in _ENABLED else ky
        if "1024" in a_norm and (ml in _ENABLED or ky in _ENABLED): return ml if ml in _ENABLED else ky
    raise ValueError(f"KEM algorithm not supported here: {alg}. Enabled: {_ENABLED}")

def kem_generate(alg: str = "ml-kem-768"):
    alg = _norm_alg(alg)
    with KeyEncapsulation(alg) as kem:
        pub = kem.generate_keypair()
        sec = kem.export_secret_key()
    return pub, sec

def kem_encapsulate(pub_b: bytes, alg: str = "ml-kem-768"):
    alg = _norm_alg(alg)
    with KeyEncapsulation(alg) as kem:
        # oqs 0.10.x: encap_secret(public_key)
        ct, shared = kem.encap_secret(pub_b)
    return ct, shared

def kem_decapsulate(ct_b: bytes, sec_b: bytes, alg: str = "ml-kem-768"):
    alg = _norm_alg(alg)
    # oqs 0.10.x: подаваме secret_key в конструктора и викaме decap_secret(ciphertext)
    with KeyEncapsulation(alg, secret_key=sec_b) as kem:
        shared = kem.decap_secret(ct_b)
    return shared

def b64e(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")

def b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))
