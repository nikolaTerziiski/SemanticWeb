#!/usr/bin/env python3
"""
build_index.py

Изгражда FAISS индекс от surface_forms.csv:
  1) Чете всички повърхностни форми (surface forms)
  2) Вика локалния LMStudio /v1/embeddings endpoint
  3) Съхранява FAISS индекс + JSON с формите
"""

import requests
import json
import numpy as np
import faiss
import csv
import os

# --- 1) Настройки ---
API_URL = "http://localhost:1234/v1/embeddings"
MODEL   = "local-embeddings"  # Както LM Studio връща в "model" полето
INPUT_CSV = "resources/surface_forms.csv"
INDEX_FILE = "resources/ont_index.faiss"
LABELS_FILE = "resources/labels.json"

# --- 2) Зареждаме surface forms ---
labels = []
with open(INPUT_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    # Очакваме колонка "form"
    for row in reader:
        labels.append(row["form"])

print(f"Loaded {len(labels)} surface forms.")

# --- 3) Викаме embedding endpoint ---
payload = {
    "model": MODEL,
    "input": labels
}
resp = requests.post(API_URL, json=payload)
resp.raise_for_status()
data = resp.json()["data"]

# --- 4) Извличаме embedding матрицата ---
#   data[i]["embedding"] е списък от float
vectors = np.array([item["embedding"] for item in data], dtype="float32")
dim = vectors.shape[1]
print(f"Received embeddings with dim={dim}.")

# --- 5) Строим FAISS индекс ---
index = faiss.IndexFlatIP(dim)        # inner-product (cosine след нормализация)
# (ако искаме cosine, можем да нормираме матрицата: faiss.normalize_L2(vectors))
index.add(vectors)
print(f"FAISS index: added {index.ntotal} vectors.")

# --- 6) Съхраняваме индекс и labels.json ---
os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
faiss.write_index(index, INDEX_FILE)
with open(LABELS_FILE, "w", encoding='utf-8') as f:
    json.dump(labels, f, ensure_ascii=False, indent=2)

print(f"Saved index to {INDEX_FILE}")
print(f"Saved labels to {LABELS_FILE}")
