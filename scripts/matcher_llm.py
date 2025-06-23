#!/usr/bin/env python3
"""
matcher_llm.py

За подаден текстов файл:
  • embed → FAISS top-k → (опц.) LLM Yes/No → span детекция
  • записва JSON [{doc,start,end,uri}, …]
"""

import argparse, json, re, os, requests, faiss, numpy as np
from pathlib import Path
import nltk; nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

EMB_API = "http://localhost:1234/v1/embeddings"
CHAT_API = "http://localhost:1234/v1/chat/completions"
EMB_MODEL = "local-embeddings"
CHAT_MODEL = "local-chat"           # кой чат-LLM e зареден

def embed(texts):
    r = requests.post(EMB_API, json={"model": EMB_MODEL, "input": texts})
    r.raise_for_status()
    return np.array([d["embedding"] for d in r.json()["data"]], dtype="float32")

def disamb(sentence, uri, form):
    prompt = [
      {"role":"system","content":"You are an ontology assistant."},
      {"role":"user",
       "content":f'In the sentence "{sentence}" does the string "{form}" refer to the concept <{uri}>? Answer Yes or No.'}
    ]
    try:
        r = requests.post(CHAT_API, json={"model": CHAT_MODEL, "messages": prompt, "max_tokens":1})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip().lower().startswith("y")
    except Exception:
        return True     # fallback: при грешка приеми Yes

def all_spans(sent, form):
    for m in re.finditer(re.escape(form), sent, flags=re.I):
        yield m.start(), m.end()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc", help="path to .txt")
    ap.add_argument("--index", default="resources/ont_index.faiss")
    ap.add_argument("--labels", default="resources/labels.json")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--thr",  type=float, default=0.65)
    ap.add_argument("-o", "--out", default="output")
    args = ap.parse_args()

    index = faiss.read_index(args.index)
    lbl   = json.load(open(args.labels, encoding="utf-8"))
    forms, uris = lbl["forms"], lbl["uris"]

    text = Path(args.doc).read_text(encoding="utf-8")
    sentences = sent_tokenize(text)

    sent_vecs = embed(sentences)
    faiss.normalize_L2(sent_vecs)
    D, I = index.search(sent_vecs, args.topk)

    preds = []
    for sent, sims, idxs in zip(sentences, D, I):
        for score, idx in zip(sims, idxs):
            if score < args.thr:            # семантичен праг
                continue
            form, uri = forms[idx], uris[idx]
            if not disamb(sent, uri, form):
                continue
            for s, e in all_spans(sent, form):
                preds.append({"doc": os.path.basename(args.doc), "start": s, "end": e, "uri": uri})

    Path(args.out).mkdir(exist_ok=True)
    out_file = Path(args.out) / (Path(args.doc).stem + "_llm.json")
    json.dump(preds, out_file.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(preds)} анотации => {out_file}")

if __name__ == "__main__":
    main()
