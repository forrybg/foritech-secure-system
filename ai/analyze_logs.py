from transformers import pipeline

classifier = pipeline("text-classification", model="distilbert-base-uncased")
with open("/app/logs.txt") as f:
    logs = f.readlines()

for line in logs:
    result = classifier(line)
    if result[0]['label'] == 'NEGATIVE':
        print(f"⚠️ Suspicious log: {line.strip()}")
