import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

models = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "neuml/pubmedbert-base-embeddings"
]

for m in models:
    url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{m}"
    resp = requests.post(url, headers=headers, json={"inputs": "test string"})
    print(f"pipeline/feature-extraction - {m}: {resp.status_code}")
    if resp.status_code == 200:
        print("  Length:", len(resp.json()))

