#!/usr/bin/env python3
"""
build_index.py

1) Чете resources/surface_forms.csv (колони: uri,form)
2) Извиква /v1/embeddings на LM Studio за списъка от форми
3) Строи FAISS индекс и записва:
      • resources/ont_index.faiss
      • resources/labels.json   {"forms":[...], "uris":[...]}
"""

import csv, json, os, requests, numpy as np, faiss

# --- настройки ---
API_URL      = "http://localhost:1234/v1/embeddings"
EMB_MODEL    = "local-embeddings"
CSV_IN       = "resources/surface_forms.csv"
INDEX_OUT    = "resources/ont_index.faiss"
LABELS_JSON  = "resources/labels.json"

# --- 1. четем CSV ---
forms, uris = [], []
with open(CSV_IN, newline='', encoding="utf-8") as f:
    for row in csv.DictReader(f):
        forms.append(row["form"])
        uris.append(row["uri"])
print(f"Loaded {len(forms)} surface forms.")

# --- 2. embeddings ---
resp = requests.post(API_URL, json={"model": EMB_MODEL, "input": forms})
resp.raise_for_status()
vectors = np.array([d["embedding"] for d in resp.json()["data"]], dtype="float32")

# --- 3. нормализираме → индекс ---
faiss.normalize_L2(vectors)              # cosine similarity
index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)

# --- 4. запис ---
os.makedirs(os.path.dirname(INDEX_OUT), exist_ok=True)
faiss.write_index(index, INDEX_OUT)
with open(LABELS_JSON, "w", encoding="utf-8") as f:
    json.dump({"forms": forms, "uris": uris}, f, ensure_ascii=False, indent=2)

print(f"Saved FAISS index → {INDEX_OUT}")
print(f"Saved labels      → {LABELS_JSON}  (forms + uris)")
