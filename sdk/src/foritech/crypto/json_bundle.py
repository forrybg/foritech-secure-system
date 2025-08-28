import base64
import json
from typing import Dict

def to_b64(b: bytes) -> str:
    return base64.b64encode(b).decode()

def from_b64(s: str) -> bytes:
    return base64.b64decode(s)

def make_bundle(alg: str, data: bytes, rsa_pub_pem: bytes, pqc_pub: bytes, sigs: Dict[str, bytes]) -> str:
    obj = {
        "version": "1.0",
        "alg": alg,
        "data_b64": to_b64(data),
        "keys": {
            "rsa_pub_pem": rsa_pub_pem.decode(),
            "pqc_pub_b64": to_b64(pqc_pub),
        },
        "sigs": {
            "rsa_b64": to_b64(sigs["rsa"]),
            "pqc_b64": to_b64(sigs["pqc"]),
        },
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)

def parse_bundle(s: str):
    obj = json.loads(s)
    data = from_b64(obj["data_b64"])
    rsa_pem = obj["keys"]["rsa_pub_pem"].encode()
    pqc_pub = from_b64(obj["keys"]["pqc_pub_b64"])
    rsa_sig = from_b64(obj["sigs"]["rsa_b64"])
    pqc_sig = from_b64(obj["sigs"]["pqc_b64"])
    return obj["alg"], data, rsa_pem, pqc_pub, {"rsa": rsa_sig, "pqc": pqc_sig}
