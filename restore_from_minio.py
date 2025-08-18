import base64
import requests

VAULT_URL = "http://127.0.0.1:8200"
VAULT_TOKEN = "root"
KEY_NAME = "foritech-key"

def decrypt_data(ciphertext):
    url = f"{VAULT_URL}/v1/transit/decrypt/{KEY_NAME}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    payload = {"ciphertext": ciphertext}
    response = requests.post(url, json=payload, headers=headers)
    plaintext_b64 = response.json()["data"]["plaintext"]
    return base64.b64decode(plaintext_b64).decode()

#iztegli fail ot  milano
from minio import Minio

client = Minio("192.168.5.9:9000", access_key="admin", secret_key="secret123", secure=False)
object_name = "logs-20250818-1746.txt"
temp_file = f"/tmp/{object_name}"

client.fget_object("foritech-backups", object_name, temp_file)

with open(temp_file, "r") as f:
    encrypted_content = f.read()

original_data = decrypt_data(encrypted_content)

# Запиши оригиналния файл
with open(f"restored-{object_name}", "w") as f:
    f.write(original_data)

print(f"✅ Файлът '{object_name}' е декриптиран и възстановен като 'restored-{object_name}'")
