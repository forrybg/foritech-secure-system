from __future__ import annotations
import base64, json
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509 import UnrecognizedExtension
from cryptography.x509.oid import NameOID, ObjectIdentifier

from ..errors import ForitechError

# Extension OID (JSON payload)
OID_FORITECH_HYBRID = ObjectIdentifier("1.3.6.1.4.1.57264.1.1")
# AlgorithmIdentifier OID за нашия вътрешен SPKI контейнер (DER SubjectPublicKeyInfo)
OID_FORITECH_PQC_SPKI = "1.3.6.1.4.1.57264.1.100"

def _now_utc():
    return datetime.now(timezone.utc)

def generate_hybrid_selfsigned(
    cn: str,
    kem_name: str,
    pqc_pubkey_bytes: bytes,
    days_valid: int = 365,
    ext_format: str = "raw",  # "raw" | "spki"
) -> Tuple[bytes, bytes]:
    """
    Генерира self-signed ECDSA (P-256) leaf с нашия хибриден extension.
    Връща (cert_pem, key_pem).
    """
    try:
        priv = ec.generate_private_key(ec.SECP256R1())
        pub = priv.public_key()

        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
        not_before = _now_utc()
        not_after  = not_before + timedelta(days=days_valid)

        if ext_format == "spki":
            spki_der = _spki_wrap(pqc_pubkey_bytes, kem_name)
            ext_payload = {
                "kem": kem_name,
                "spki_b64": base64.b64encode(spki_der).decode("ascii"),
                "format": "spki-b64",
                "v": 1,
            }
        else:
            ext_format = "raw"
            ext_payload = {
                "kem": kem_name,
                "pqc_pub_b64": base64.b64encode(pqc_pubkey_bytes).decode("ascii"),
                "format": "raw",
                "v": 1,
            }

        hybrid_ext = UnrecognizedExtension(
            OID_FORITECH_HYBRID,
            json.dumps(ext_payload, separators=(",", ":")).encode("utf-8"),
        )

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(pub)
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(hybrid_ext, critical=False)
        )
        cert = builder.sign(private_key=priv, algorithm=hashes.SHA256())

        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
        key_pem  = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return cert_pem, key_pem
    except Exception as e:
        raise ForitechError(f"PKI self-signed error: {e}") from e

def extract_hybrid_info(cert_pem_or_der: bytes) -> Optional[dict]:
    """
    Връща JSON payload от нашия OID или None. Ако е spki-b64, правим лека валидация.
    """
    try:
        try:
            cert = x509.load_pem_x509_certificate(cert_pem_or_der)
        except ValueError:
            cert = x509.load_der_x509_certificate(cert_pem_or_der)
        ext = cert.extensions.get_extension_for_oid(OID_FORITECH_HYBRID).value
        if isinstance(ext, UnrecognizedExtension):
            info = json.loads(ext.value.decode("utf-8"))
            if info.get("format") == "spki-b64" and "spki_b64" in info:
                try:
                    _ = _spki_unwrap(base64.b64decode(info["spki_b64"]))
                except Exception:
                    pass
            return info
        return None
    except x509.ExtensionNotFound:
        return None
    except Exception as e:
        raise ForitechError(f"PKI extract error: {e}") from e

def generate_ca_selfsigned(cn: str, days_valid: int = 3650) -> tuple[bytes, bytes]:
    """
    Генерира self-signed ECDSA CA (P-256). Връща (ca_cert_pem, ca_key_pem).
    """
    try:
        priv = ec.generate_private_key(ec.SECP256R1())
        pub = priv.public_key()
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
        not_before = _now_utc()
        not_after  = not_before + timedelta(days=days_valid)
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(pub)
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False
            ), critical=True)
        )
        cert = builder.sign(private_key=priv, algorithm=hashes.SHA256())
        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
        key_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return cert_pem, key_pem
    except Exception as e:
        raise ForitechError(f"PKI CA generate error: {e}") from e

def issue_leaf_cert(
    ca_cert_pem: bytes,
    ca_key_pem: bytes,
    subject_cn: str,
    kem_name: str,
    pqc_pubkey_bytes: bytes,
    days_valid: int = 825,
    ext_format: str = "raw",  # "raw" | "spki"
) -> bytes:
    """
    Издава leaf сертификат, подписан от даден CA, с нашия hybrid extension.
    Връща PEM на издадения leaf.
    """
    try:
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
        ca_key = serialization.load_pem_private_key(ca_key_pem, password=None)
        if not isinstance(ca_key, ec.EllipticCurvePrivateKey):
            raise ForitechError("CA key must be EC P-256 private key")

        leaf_priv = ec.generate_private_key(ec.SECP256R1())
        leaf_pub  = leaf_priv.public_key()

        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)])
        issuer  = ca_cert.subject
        not_before = _now_utc()
        not_after  = not_before + timedelta(days=days_valid)

        if ext_format == "spki":
            spki_der = _spki_wrap(pqc_pubkey_bytes, kem_name)
            ext_payload = {
                "kem": kem_name,
                "spki_b64": base64.b64encode(spki_der).decode("ascii"),
                "format": "spki-b64",
                "v": 1,
            }
        else:
            ext_format = "raw"
            ext_payload = {
                "kem": kem_name,
                "pqc_pub_b64": base64.b64encode(pqc_pubkey_bytes).decode("ascii"),
                "format": "raw",
                "v": 1,
            }

        hybrid_ext = UnrecognizedExtension(
            OID_FORITECH_HYBRID,
            json.dumps(ext_payload, separators=(",", ":")).encode("utf-8"),
        )
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(leaf_pub)
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(hybrid_ext, critical=False)
        )
        leaf = builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
        return leaf.public_bytes(encoding=serialization.Encoding.PEM)
    except ForitechError:
        raise
    except Exception as e:
        raise ForitechError(f"Issue leaf error: {e}") from e

# ===== SPKI helpers (минимален DER encoder/decoder) =====

def _der_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    out = []
    while n > 0:
        out.append(n & 0xFF)
        n >>= 8
    out = bytes(reversed(out))
    return bytes([0x80 | len(out)]) + out

def _der_oid(oid: str) -> bytes:
    parts = [int(x) for x in oid.split(".")]
    if len(parts) < 2:
        raise ValueError("bad OID")
    first = 40*parts[0] + parts[1]
    body = [first]
    for p in parts[2:]:
        if p == 0:
            body.append(0)
            continue
        stack = []
        while p > 0:
            stack.append(0x80 | (p & 0x7F))
            p >>= 7
        stack[0] &= 0x7F
        body.extend(reversed(stack))
    enc = bytes(body)
    return bytes([0x06]) + _der_len(len(enc)) + enc

def _der_utf8(s: str) -> bytes:
    b = s.encode("utf-8")
    return bytes([0x0C]) + _der_len(len(b)) + b

def _der_seq(*children: bytes) -> bytes:
    payload = b"".join(children)
    return bytes([0x30]) + _der_len(len(payload)) + payload

def _der_bit_string(data: bytes) -> bytes:
    payload = b"\x00" + data  # 0 unused bits
    return bytes([0x03]) + _der_len(len(payload)) + payload

def _spki_wrap(pub: bytes, kem_name: str) -> bytes:
    # SubjectPublicKeyInfo ::= SEQUENCE { algorithm AlgorithmIdentifier, subjectPublicKey BIT STRING }
    # AlgorithmIdentifier ::= SEQUENCE { algorithm OBJECT IDENTIFIER, parameters UTF8String kem_name }
    alg = _der_seq(_der_oid(OID_FORITECH_PQC_SPKI), _der_utf8(kem_name))
    return _der_seq(alg, _der_bit_string(pub))

def _spki_unwrap(spki_der: bytes) -> Tuple[str, bytes]:
    b = memoryview(spki_der)

    def read_seq(offset):
        if b[offset] != 0x30:
            raise ValueError("SPKI: expected SEQUENCE")
        l = b[offset+1]
        if l & 0x80:
            n = l & 0x7F
            ln = int.from_bytes(b[offset+2:offset+2+n], "big")
            start = offset+2+n
        else:
            ln = l
            start = offset+2
        return start, start+ln

    s0, e0 = read_seq(0)          # outer SEQ
    s1, e1 = read_seq(s0)         # alg SEQ
    # OID
    if b[s1] != 0x06:
        raise ValueError("SPKI: expected OID")
    l1 = b[s1+1]
    if l1 & 0x80:
        n = l1 & 0x7F
        oid_end = s1+2+n+int.from_bytes(b[s1+2:s1+2+n],'big')
    else:
        oid_end = s1+2+l1
    # UTF8 kem_name
    if b[oid_end] != 0x0C:
        raise ValueError("SPKI: expected UTF8 kem_name")
    l2 = b[oid_end+1]
    if l2 & 0x80:
        n = l2 & 0x7F
        ulen = int.from_bytes(b[oid_end+2:oid_end+2+n],'big')
        ustart = oid_end+2+n
    else:
        ulen = l2
        ustart = oid_end+2
    kem_name = bytes(b[ustart:ustart+ulen]).decode("utf-8")
    # BIT STRING
    p = e1
    if b[p] != 0x03:
        raise ValueError("SPKI: expected BIT STRING")
    l3 = b[p+1]
    if l3 & 0x80:
        n = l3 & 0x7F
        blen = int.from_bytes(b[p+2:p+2+n],'big')
        bstart = p+2+n
    else:
        blen = l3
        bstart = p+2
    if b[bstart] != 0x00:
        raise ValueError("SPKI: non-zero unused bits")
    pub = bytes(b[bstart+1:bstart+blen])
    return kem_name, pub
