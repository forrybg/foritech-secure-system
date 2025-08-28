# PKI Rotation (Quick Playbook)

This repo uses a Root -> Issuing (Sub-CA) -> Leaf chain for the demo TLS-PQC server.
For seamless updates, the server always reads `server_cert.pem` and `server_key.pem`,
which are symlinks you can repoint during rotation.

## A) Issue a new leaf from your Issuing CA

Example:
```bash
foritech x509-issue --cn "leaf-sub1" --kem Kyber768 --format spki \
  --pqc-pub "$HOME/.foritech/keys/kyber768_pub.bin" \
  --ca-cert pki/subca/subca.pem --ca-key pki/subca/subca.key \
  --cert-out pki/issued/leaf-sub1.pem --chain-out pki/issued/leaf-sub1_fullchain.pem

Rotate the server symlinks
scripts/ca_rotate_symlinks.sh \
  pki/issued/leaf-sub1.pem \
  pki/issued/leaf-sub1.key \
  pki/issued/leaf-sub1_fullchain.pem

If pki/root/root.pem exists, the script will verify the chain before switching.
C) Run the demo
# Terminal 1
export FORITECH_SK="$HOME/.foritech/keys/kyber768_sec.bin"
scripts/demo_run_server.sh

# Terminal 2
scripts/demo_run_client.sh

You should see the KEM info and a pong/OK.

Notes

Keep Root and Issuing private keys offline where possible.

Only symlinks are updated on rotation; no code changes required.

For production, add CRLs/OCSP and automate renewal windows.
