# Foritech PKI: Root + Sub-CA + Leaf

## 0) Prereqs
Have a Root CA (self-signed):

foritech x509-make-ca --cn "Foritech Root CA 2025"
--cert-out pki/root/root.pem --key-out pki/root/root.key

## 1) Create Sub-CA (signed by Root)

bash scripts/ca_make_subca.sh "Foritech Issuing CA 1"

## 2) Issue a leaf from Sub-CA (embed PQC key)
Format can be `spki` (recommended) or `raw`:

bash scripts/ca_issue_from_subca.sh "leaf-sub1" "$HOME/.foritech/keys/kyber768_pub.bin" spki
Artifacts:
- `pki/issued/leaf-sub1.pem` (leaf)
- `pki/issued/leaf-sub1_chain.pem` (leaf + Sub-CA)
- `pki/issued/leaf-sub1_fullchain.pem` (leaf + Sub-CA + Root)

## 3) Verify

bash scripts/x509_verify_chain.sh pki/issued/leaf-sub1.pem
pki/issued/leaf-sub1_fullchain.pem pki/root/root.pem

## Notes
- Keep Root offline when possible. Sign Sub-CAs in controlled env.
- Rotate Sub-CA on policy. Track serials, CRL/OCSP if needed later.
- PQC public key is carried in Foritech extension (raw/SPKI).
