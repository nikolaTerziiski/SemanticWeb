#!/usr/bin/env python3
"""
Generate embeddings for ontology surface forms and build a FAISS index.

The script reads ``resources/surface_forms.csv``, fetches embeddings from
LM Studio's ``/v1/embeddings`` API, normalizes the vectors for cosine
similarity, builds a FAISS index and writes both the index and a JSON
file with the original forms and their URIs.
"""

import requests, json, csv, os
import numpy as np
import faiss                         # pip install faiss-cpu
from pathlib import Path

API_URL   = "http://localhost:1234/v1/embeddings"
MODEL     = "local-embeddings"
INPUT_CSV = Path("resources/surface_forms.csv")
INDEX_OUT = Path("resources/ont_index.faiss")
LABELS_JS = Path("resources/labels.json")

# --- 1. зареждаме форми и URI-та ---
forms, uris = [], []
with INPUT_CSV.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        forms.append(row["form"])
        uris.append(row["uri"])

# --- 2. викаме embeddings ---
resp = requests.post(API_URL, json={"model": MODEL, "input": forms})
resp.raise_for_status()
vectors = np.array([d["embedding"] for d in resp.json()["data"]], dtype="float32")

# --- 3. нормализация + индекс ---
faiss.normalize_L2(vectors)                                    # cosine sim
dim   = vectors.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(vectors)

# --- 4. запис ---
INDEX_OUT.parent.mkdir(exist_ok=True, parents=True)
faiss.write_index(index, str(INDEX_OUT))
json.dump({"forms": forms, "uris": uris}, LABELS_JS.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"FAISS index => {INDEX_OUT} ; labels => {LABELS_JS}")
