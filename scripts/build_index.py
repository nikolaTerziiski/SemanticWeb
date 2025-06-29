#!/usr/bin/env python3
"""
build_index.py

Build a FAISS IndexFlatIP (cosine similarity) over ontology surface forms
and save it as ont_index.faiss plus a parallel labels.json mapping.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

# --- Start of Changes ---
# Add project root to path to allow imports from other directories
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
# --- End of Changes ---

import faiss
import numpy as np
import requests


def embed(texts, endpoint, model):
    payload = {"input": texts, "model": model}
    res = requests.post(endpoint, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()["data"]
    return np.array([d["embedding"] for d in data], dtype="float32")


def main():
    ap = argparse.ArgumentParser()
    # --- Start of Changes ---
    # Use ROOT to define default paths
    ap.add_argument("csv", type=Path, default=ROOT / "resources/surface_forms.csv", nargs='?')
    ap.add_argument("--endpoint", default="http://localhost:1234/v1/embeddings")
    ap.add_argument("--model", default="local-embedding-model")
    ap.add_argument("-o", "--out_dir", type=Path, default=ROOT / "resources")
    # --- End of Changes ---
    args = ap.parse_args()

    forms, uris = [], []
    # --- Change ---
    csv_path = args.csv
    # --- End Change ---
    with csv_path.open(encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            uris.append(row["uri"])
            forms.append(row["form"])

    print(f"Embedding {len(forms)} surface forms…")
    vecs = embed(forms, args.endpoint, args.model)

    # L2 normalise for cosine similarity
    faiss.normalize_L2(vecs)

    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)

    args.out_dir.mkdir(exist_ok=True)
    # --- Change ---
    faiss_out_path = args.out_dir / "ont_index.faiss"
    labels_out_path = args.out_dir / "labels.json"
    faiss.write_index(index, str(faiss_out_path))
    # --- End Change ---

    with labels_out_path.open("w", encoding="utf-8") as fh:
        json.dump({"forms": forms, "uris": uris}, fh, ensure_ascii=False, indent=2)

    print(f"Index written to {faiss_out_path}")
    print(f"Labels written to {labels_out_path}")


if __name__ == "__main__":
    main()