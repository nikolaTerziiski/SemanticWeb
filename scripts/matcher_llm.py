#!/usr/bin/env python3
"""
matcher_llm.py

Given a plain‑text document, find occurrences of ontology surface forms
using semantic search + optional chat disambiguation and write
OpenAnnotation‑ready JSON.
"""
import argparse
import json
import re
from pathlib import Path
import sys

# --- Start of Changes ---
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
# --- End of Changes ---

import faiss
import numpy as np
import nltk
import requests

# --- Change: Use ROOT for paths ---
RESOURCES_DIR = ROOT / "resources"
OUTPUT_DIR = ROOT / "output"
# --- End Change ---

nltk.download("punkt", quiet=True)


def embed(texts, endpoint, model):
    payload = {"input": texts, "model": model}
    res = requests.post(endpoint, json=payload, timeout=120)
    res.raise_for_status()
    return np.array([d["embedding"] for d in res.json()["data"]], dtype="float32")


def yesno(prompt, endpoint, model="local-chat"):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 1,
    }
    res = requests.post(endpoint, json=payload, timeout=60)
    res.raise_for_status()
    answer = res.json()["choices"][0]["message"]["content"].strip().lower()
    return answer.startswith("y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc", type=Path)
    ap.add_argument("--topk", type=int, default=5, help="number of nearest ontology labels to consider")
    ap.add_argument("--thr", type=float, default=0.65, help="cosine threshold below which to reject candidates")
    ap.add_argument("--endpoint", default="http://localhost:1234/v1/embeddings")
    ap.add_argument("--embed_model", default="local-embedding-model")
    ap.add_argument("--chat_endpoint", default="http://localhost:1234/v1/chat/completions")
    ap.add_argument("--no-chat", action="store_true")
    args = ap.parse_args()

    # --- Change: Use ROOT-based paths ---
    labels_path = RESOURCES_DIR / "labels.json"
    index_path = RESOURCES_DIR / "ont_index.faiss"

    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    # --- End Change ---
    forms = labels["forms"]
    uris = labels["uris"]

    index = faiss.read_index(str(index_path))

    text = args.doc.read_text(encoding="utf-8")
    sentences = nltk.tokenize.sent_tokenize(text)
    sent_vecs = embed(sentences, args.endpoint, args.embed_model)
    faiss.normalize_L2(sent_vecs)

    annos = []
    for sent, vec in zip(sentences, sent_vecs):
        D, I = index.search(vec.reshape(1, -1), args.topk)
        for score, idx in zip(D[0], I[0]):
            if score < args.thr:
                continue
            form = forms[idx]
            uri = uris[idx]
            if not args.no_chat:
                q = f'Does the phrase "{form}" in the sentence "{sent}" refer to the wine concept "{uri.split("/")[-1]}"? Answer Yes or No.'
                if not yesno(q, args.chat_endpoint):
                    continue
            for m in re.finditer(re.escape(form), sent, flags=re.IGNORECASE):
                start_offset = text.find(sent)
                if start_offset == -1: continue # Should not happen
                start = start_offset + m.start()
                end = start_offset + m.end()
                annos.append({"doc": args.doc.name, "start": start, "end": end, "form": m.group(0), "uri": uri, "score": float(score)})

    # --- Change: Use ROOT-based path ---
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_file = OUTPUT_DIR / f"{args.doc.stem}_llm.json"
    # --- End Change ---
    out_file.write_text(json.dumps(annos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(annos)} annotations to {out_file}")


if __name__ == "__main__":
    main()