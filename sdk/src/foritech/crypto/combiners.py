from typing import Tuple

class SignatureCombiner:
    def __init__(self, scheme_a, scheme_b):
        self.a = scheme_a
        self.b = scheme_b

    def sign(self, msg: bytes) -> Tuple[bytes, bytes]:
        return self.a.sign(msg), self.b.sign(msg)

    def verify(self, msg: bytes, sig_a: bytes, sig_b: bytes) -> bool:
        return self.a.verify(msg, sig_a) and self.b.verify(msg, sig_b)
