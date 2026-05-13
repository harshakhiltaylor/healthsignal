import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
token = os.getenv("HF_TOKEN")

client = InferenceClient(token=token)

try:
    print("Testing sentence-transformers/all-MiniLM-L6-v2")
    res = client.feature_extraction(
        model="sentence-transformers/all-MiniLM-L6-v2",
        text="test string"
    )
    print("Success:", len(res))
except Exception as e:
    print("Error:", e)

try:
    print("Testing neuml/pubmedbert-base-embeddings")
    res = client.feature_extraction(
        model="neuml/pubmedbert-base-embeddings",
        text="test string"
    )
    print("Success:", len(res))
except Exception as e:
    print("Error:", e)

