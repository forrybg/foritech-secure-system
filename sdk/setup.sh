#!/bin/bash
# setup.sh – автоматичен patch за ForiTech SDK
# Внимавай: ще модифицира файловете x509_tools.py и cli.py

set -e  # ако нещо гръмне, спира

echo "[1/2] Пачваме x509_tools.py (UTC warning fix)..."
X509="src/foritech/pki/x509_tools.py"
if grep -q "datetime.utcnow()" "$X509"; then
  sed -i 's/from datetime import datetime, timedelta/from datetime import datetime, timedelta, timezone/' "$X509"
  sed -i 's/datetime.utcnow()/datetime.now(timezone.utc)/g' "$X509"
  echo "✔ Patched $X509"
else
  echo "⏩ Already patched $X509"
fi

echo "[2/2] Добавяме CLI команди в cli.py..."
CLI="src/foritech/cli.py"
if ! grep -q "hybrid-sign" "$CLI"; then
  cat >> "$CLI" << 'PY'

from .crypto.hybrid_sig import HybridSignature
import base64

@app.command("hybrid-sign")
def hybrid_sign(data: str = "hello", alg: str = "Dilithium2"):
    """Sign data with hybrid (RSA + PQC) and print base64 signatures."""
    hs = HybridSignature(alg)
    sigs = hs.sign(data.encode())
    print("RSA:", base64.b64encode(sigs["rsa"]).decode())
    print("PQC:", base64.b64encode(sigs["pqc"]).decode())

@app.command("hybrid-verify")
def hybrid_verify(data: str, rsa_sig_b64: str, pqc_sig_b64: str, alg: str = "Dilithium2"):
    """Verify base64 RSA and PQC signatures for given data."""
    hs = HybridSignature(alg)
    ok = hs.verify(
        data.encode(),
        {
            "rsa": base64.b64decode(rsa_sig_b64),
            "pqc": base64.b64decode(pqc_sig_b64),
        },
    )
    print("OK" if ok else "FAIL")
PY
  echo "✔ Added hybrid-sign and hybrid-verify to $CLI"
else
  echo "⏩ Commands already exist in $CLI"
fi

echo "✅ Setup script completed!"
