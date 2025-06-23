#!/usr/bin/env python3
"""
matcher_llm.py

За всеки документ:
  1) Делим текста на изречения
  2) Правим embedding на всяко изречение
  3) Търсим top-k кандидата в FAISS
  4) (по избор) пращаме chat-заявка за дизамбиуация
  5) Записваме резултата в JSON
"""

import requests
import json
import numpy as np
import faiss
import sys
import os
import nltk

# --- Настройки ---
API_URL_EMB = "http://localhost:1234/v1/embeddings"
EMB_MODEL   = "local-embeddings"
FAISS_INDEX = "resources/ont_index.faiss"
LABELS_FILE = "resources/labels.json"
OUTPUT_DIR  = "output"
TOP_K       = 5

# Initialize sentence tokenizer (изисква да сте инсталирали nltk punkt)
nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

def load_index():
    """Зарежда FAISS индекс и labels.json."""
    index = faiss.read_index(FAISS_INDEX)
    with open(LABELS_FILE, encoding='utf-8') as f:
        labels = json.load(f)
    return index, labels

def embed_texts(texts):
    """Обща функция за embeddings на списък от текстове."""
    resp = requests.post(API_URL_EMB, json={
        "model": EMB_MODEL,
        "input": texts
    })
    resp.raise_for_status()
    data = resp.json()["data"]
    return np.array([item["embedding"] for item in data], dtype="float32")

def process_document(doc_path, index, labels):
    """Връща списък от ангажирания (sentence, top_k list)."""
    text = open(doc_path, encoding='utf-8').read()
    sentences = sent_tokenize(text)
    # 1) Вземаме embeddings за целия списък
    emb = embed_texts(sentences)
    # (по желание: faiss.normalize_L2(emb))
    # 2) Търсим Top-K кандидати за всяка embedding
    D, I = index.search(emb, TOP_K)
    results = []
    for sent, distances, idxs in zip(sentences, D, I):
        candidates = []
        for score, idx in zip(distances, idxs):
            candidates.append({
                "label": labels[idx],
                "score": float(score)
            })
        results.append({
            "sentence": sent,
            "candidates": candidates
        })
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python matcher_llm.py path/to/document.txt")
        sys.exit(1)
    doc_path = sys.argv[1]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index, labels = load_index()
    matches = process_document(doc_path, index, labels)

    # Записваме резултат в JSON
    name = os.path.splitext(os.path.basename(doc_path))[0]
    out_file = os.path.join(OUTPUT_DIR, f"{name}_llm.json")
    with open(out_file, "w", encoding='utf-8') as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(matches)} sentence matches to {out_file}")

if __name__ == "__main__":
    main()
