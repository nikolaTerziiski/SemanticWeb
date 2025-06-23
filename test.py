import requests

url = "http://127.0.0.1:1234/v1/embeddings"
payload = {
    "model": "text-embedding-nomic-embed-text-v1.5",
    "input": ["Some text to embed"]
}
resp = requests.post(url, json=payload)
print(resp.status_code, resp.json())
