from dataclasses import dataclass, field
from typing import Optional, List, Union

@dataclass
class KemPolicy:
    algos: List[str] = field(default_factory=lambda: ["Kyber768"])
    prefer_ordered: bool = True
    require_pqc: bool = True

@dataclass
class WrapParams:
    kid: Optional[str] = None
    aad: Optional[bytes] = None
    kem_policy: KemPolicy = field(default_factory=KemPolicy)

@dataclass
class UnwrapParams:
    allow_fallback: bool = True

@dataclass
class WrapResult:
    kid: Optional[str]; nonce: Optional[str]; aad_present: bool; kem: str

@dataclass
class UnwrapResult:
    recovered_kid: Optional[str]; aad_present: bool; kem: str

@dataclass
class RawKemRecipient:
    public_key_path: str

@dataclass
class X509Recipient:
    pem_path: str

Recipient = Union[RawKemRecipient, X509Recipient]
