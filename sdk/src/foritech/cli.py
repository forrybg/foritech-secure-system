from typer import Typer
from .pki.x509_tools import generate_hybrid_cert

app = Typer(help="ForiTech Secure System CLI")

@app.command()
def hybrid_cert(common_name: str = "example.com"):
    """Generate a demo (placeholder) hybrid certificate PEM."""
    pem = generate_hybrid_cert(common_name)
    print(pem)

if __name__ == "__main__":
    app()

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
    print("already naked — is the plane flying?" if ok else "FAIL")


from cryptography.hazmat.primitives import serialization
import base64

@app.command("hybrid-keys")
def hybrid_keys(alg: str = "Dilithium2"):
    """Генерира и отпечатва публичните ключове (RSA PEM + PQC raw b64) за текущата сесия."""
    hs = HybridSignature(alg)
    rsa_pem = hs.rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pqc_b64 = base64.b64encode(hs.pqc_public_key).decode()
    print("RSA_PEM_BEGIN")
    print(rsa_pem.decode().strip())
    print("RSA_PEM_END")
    print("PQC_B64", pqc_b64)

@app.command("hybrid-verify-keys")
def hybrid_verify_keys(
    data: str,
    rsa_pub_pem_file: str,
    pqc_pub_b64: str,
    rsa_sig_b64: str,
    pqc_sig_b64: str,
    alg: str = "Dilithium2"
):
    """Верифицира подписи, като публичните ключове се подават отвън."""
    from cryptography.hazmat.primitives import serialization
    import base64
    from .crypto.hybrid_sig import verify_with_keys

    # Зареждаме RSA публичния ключ от PEM файл
    with open(rsa_pub_pem_file, "rb") as f:
        rsa_pub = serialization.load_pem_public_key(f.read())

    pqc_pub = base64.b64decode(pqc_pub_b64)
    sigs = {
        "rsa": base64.b64decode(rsa_sig_b64),
        "pqc": base64.b64decode(pqc_sig_b64),
    }
    ok = verify_with_keys(data.encode(), rsa_pub, alg, pqc_pub, sigs)
    print("already naked — is the plane flying?" if ok else "FAIL")


from cryptography.hazmat.primitives import serialization
import base64

@app.command("hybrid-sign-bundle")
def hybrid_sign_bundle(data: str = "foritech-demo", alg: str = "Dilithium2", out_file: str = "/tmp/foritech_bundle.txt"):
    """
    Генерира ЕДНА инстанция, подписва и записва В ЕДИН ФАЙЛ:
    - RSA публичен ключ (PEM)
    - PQC публичен ключ (base64)
    - Подписи (RSA b64 и PQC b64)
    - Данните (base64), алгоритъм
    """
    hs = HybridSignature(alg)
    rsa_pem = hs.rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pqc_b64 = base64.b64encode(hs.pqc_public_key).decode()
    sigs = hs.sign(data.encode())
    rsa_sig_b64 = base64.b64encode(sigs["rsa"]).decode()
    pqc_sig_b64 = base64.b64encode(sigs["pqc"]).decode()

    with open(out_file, "w") as f:
        f.write("ALG " + alg + "\n")
        f.write("DATA_B64 " + base64.b64encode(data.encode()).decode() + "\n")
        f.write("RSA_PUB_PEM_BEGIN\n")
        f.write(rsa_pem.decode())
        f.write("RSA_PUB_PEM_END\n")
        f.write("PQC_PUB_B64 " + pqc_b64 + "\n")
        f.write("RSA_SIG_B64 " + rsa_sig_b64 + "\n")
        f.write("PQC_SIG_B64 " + pqc_sig_b64 + "\n")
    print("WROTE", out_file)

@app.command("hybrid-verify-bundle")
def hybrid_verify_bundle(bundle_file: str):
    """
    Чете bundle файла и верифицира подписите срещу включените публични ключове.
    """
    import base64, re
    from cryptography.hazmat.primitives import serialization
    from .crypto.hybrid_sig import verify_with_keys

    with open(bundle_file, "r") as f:
        txt = f.read()

    alg = re.search(r'^ALG\s+(.+)$', txt, re.M).group(1).strip()
    data_b64 = re.search(r'^DATA_B64\s+(.+)$', txt, re.M).group(1).strip()
    pqc_pub_b64 = re.search(r'^PQC_PUB_B64\s+(.+)$', txt, re.M).group(1).strip()
    rsa_sig_b64 = re.search(r'^RSA_SIG_B64\s+(.+)$', txt, re.M).group(1).strip()
    pqc_sig_b64 = re.search(r'^PQC_SIG_B64\s+(.+)$', txt, re.M).group(1).strip()

    pem_block = re.search(r'RSA_PUB_PEM_BEGIN\n(.*?)\nRSA_PUB_PEM_END', txt, re.S).group(1)
    rsa_pub = serialization.load_pem_public_key(pem_block.encode())

    ok = verify_with_keys(
        base64.b64decode(data_b64),
        rsa_pub,
        alg,
        base64.b64decode(pqc_pub_b64),
        {
            "rsa": base64.b64decode(rsa_sig_b64),
            "pqc": base64.b64decode(pqc_sig_b64),
        }
    )
    print("already naked — is the plane flying?" if ok else "FAIL")


from cryptography.hazmat.primitives import serialization
from .crypto.json_bundle import make_bundle, parse_bundle
import json, sys

@app.command("hybrid-sign-json")
def hybrid_sign_json(data: str = "foritech-demo", alg: str = "Dilithium2", out_file: str = "/tmp/foritech_bundle.json"):
    """Подписва и записва bundle в JSON (ключове + подписи + данни)."""
    hs = HybridSignature(alg)
    rsa_pem = hs.rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sigs = hs.sign(data.encode())
    js = make_bundle(alg, data.encode(), rsa_pem, hs.pqc_public_key, sigs)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(js)
    print("WROTE", out_file)

@app.command("hybrid-verify-json")
def hybrid_verify_json(bundle_file: str):
    """Верифицира JSON bundle файл."""
    from cryptography.hazmat.primitives import serialization
    from .crypto.hybrid_sig import verify_with_keys
    with open(bundle_file, "r", encoding="utf-8") as f:
        js = f.read()
    alg, data, rsa_pem, pqc_pub, sigs = parse_bundle(js)
    rsa_pub = serialization.load_pem_public_key(rsa_pem)
    ok = verify_with_keys(data, rsa_pub, alg, pqc_pub, sigs)
    print("вече съм гола — самолетът лети ли?" if ok else "FAIL")
