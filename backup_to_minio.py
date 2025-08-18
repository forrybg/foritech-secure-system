from minio import Minio
from datetime import datetime
import os
import base64
import requests

# Конфигурация
MINIO_URL = "192.168.5.9:9000"
ACCESS_KEY = "admin"
SECRET_KEY = "secret123"
BUCKET_NAME = "foritech-backups"
FILE_TO_BACKUP = "/home/forybg/logs.txt"

# Инициализация
client = Minio(MINIO_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)

# Създаване на bucket ако не съществува
if not client.bucket_exists(BUCKET_NAME):
    client.make_bucket(BUCKET_NAME)

# Генериране на име с timestamp
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
object_name = f"logs-{timestamp}.txt"

#funkcia za kriptirane 
VAULT_URL = "http://127.0.0.1:8200"
VAULT_TOKEN = "root"
KEY_NAME = "foritech-key"

def encrypt_data(data):
    url = f"{VAULT_URL}/v1/transit/encrypt/{KEY_NAME}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    payload = {"plaintext": base64.b64encode(data.encode()).decode()}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()["data"]["ciphertext"]




# Качване
with open(FILE_TO_BACKUP, "r") as f:
    raw_data = f.read()

ciphertext = encrypt_data(raw_data)

# Запиши криптирания текст временно
temp_file = f"/tmp/{object_name}"
with open(temp_file, "w") as f:
    f.write(ciphertext)

# Качване в MinIO
client.fput_object(BUCKET_NAME, object_name, temp_file)
print(f"🔐 Криптиран архив '{object_name}' качен успешно в MinIO.")
