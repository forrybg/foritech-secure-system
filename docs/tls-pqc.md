# Foritech TLS-PQC (Session API)

**Цел:** Лека сесийна обвивка върху HTTPS с PQC KEM (Kyber768) за договаряне на симетричен ключ (KEK), после AEAD (ChaCha20-Poly1305) за payload-и.

## Протокол (накратко)

1. **Server cert**: X.509 с Foritech хибриден extension (Kyber pub) — `foritech x509-make --format spki`.
2. **Handshake**: клиентът капсулира към Kyber pub → `ct_b64` към `/handshake` → сървърът декриптира, получава shared secret `ss`, извежда **KEK = HKDF(ss, "foritech-kem-demo-v1")`**, връща `session_id`, `epoch=0`.
3. **Send**:
   - `/send`: единично съобщение: AEAD(KEK, nonce=12B, aad=AAD|epoch) → plaintext/rotated.
   - `/send-many`: batch кадри със свои nonces.
4. **Key Update**: по заявка (`key_update=true`) или автоматично след N съобщения. Нов ключ: `KEK' = HKDF(KEK, "foritech-keyupdate|epoch=<e>")`, `epoch++`.
5. **Bye**: `/bye` чисти сесията.

**Защити:** TTL, nonce-reuse защита (409), epoch-scoped AAD, ротация.

## Python клиент (SDK)

```python
from foritech.tlspqc import TLSPQCClient

client = TLSPQCClient("127.0.0.1", 8443)   # cafile=None за PoC
hs = client.handshake()
sess = client.session(hs)

plains, rotated = sess.send_many([b"m1", b"m2"], key_update=True)
one, rot = sess.send_one(b"final")
sess.bye()
Зависимост: liboqs-python (oqs) на клиента; сървърът също го изисква.

Server PoC

Вж. scripts/tls_pqc_server.py — TLS (Python ssl) + Kyber768 (oqs), in-mem sessions.
