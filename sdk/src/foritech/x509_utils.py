from __future__ import annotations
from typing import List, Optional, Dict
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.backends import default_backend
import datetime

def _load_all_pem(pem_bytes: bytes) -> List[x509.Certificate]:
    certs: List[x509.Certificate] = []
    rest = pem_bytes
    marker = b"-----END CERTIFICATE-----"
    while rest:
        try:
            cert = x509.load_pem_x509_certificate(rest, default_backend())
            certs.append(cert)
            idx = rest.find(marker)
            if idx == -1: break
            rest = rest[idx+len(marker):]
        except Exception:
            break
    return certs

def _verify_sig(child: x509.Certificate, issuer: x509.Certificate) -> None:
    pub = issuer.public_key()
    sig = child.signature
    data = child.tbs_certificate_bytes
    algo = child.signature_hash_algorithm
    if isinstance(pub, rsa.RSAPublicKey):
        pub.verify(sig, data, padding.PKCS1v15(), algo)
    elif isinstance(pub, ec.EllipticCurvePublicKey):
        pub.verify(sig, data, ec.ECDSA(algo))
    else:
        pub.verify(sig, data)

def verify_chain(leaf_pem: bytes, chain_pem: Optional[bytes] = None, root_pem: Optional[bytes] = None, check_time: bool = True) -> Dict[str, object]:
    leaf = x509.load_pem_x509_certificate(leaf_pem, default_backend())
    intermediates: List[x509.Certificate] = _load_all_pem(chain_pem) if chain_pem else []
    root = x509.load_pem_x509_certificate(root_pem, default_backend()) if root_pem else None
    if check_time:
        now = datetime.datetime.utcnow().replace(tzinfo=None)
        for c in [leaf] + intermediates + ([root] if root else []):
            if c and (now < c.not_valid_before.replace(tzinfo=None) or now > c.not_valid_after.replace(tzinfo=None)):
                raise ValueError(f"Certificate time invalid for {c.subject.rfc4514_string()}")
    subjects = [leaf.subject.rfc4514_string()]
    current = leaf
    depth = 0
    while True:
        if root and current.issuer == root.subject:
            _verify_sig(current, root)
            subjects.append(root.subject.rfc4514_string())
            _verify_sig(root, root)
            break
        issuer = next((ci for ci in intermediates if current.issuer == ci.subject), None)
        if issuer is None:
            if current.issuer == current.subject:
                _verify_sig(current, current)
                subjects.append(current.subject.rfc4514_string())
                break
            raise ValueError("Issuer not found in provided chain/root")
        _verify_sig(current, issuer)
        subjects.append(issuer.subject.rfc4514_string())
        current = issuer
        depth += 1
        if depth > 10:
            raise ValueError("Chain too deep / loop?")
    return {"ok": True, "depth": depth, "subjects": subjects}
