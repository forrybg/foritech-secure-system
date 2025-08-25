class ForitechError(Exception): pass
class InvalidInput(ForitechError): pass
class CryptoBackendMissing(ForitechError): pass
class RecipientNotFound(ForitechError): pass
class IntegrityError(ForitechError): pass
class UnsupportedAlgorithm(ForitechError): pass
