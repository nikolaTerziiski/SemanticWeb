#!/usr/bin/env python3
"""
evaluate.py   pred_dir/   gold_dir/
Сравнява предсказаните и златните анотации, връща P / R / F1.
"""

import argparse
import json
from pathlib import Path

def _load_file(fp: Path):
    """Return set of (doc,start,end,uri) tuples from a single JSON file."""
    data = json.load(fp.open(encoding="utf-8"))
    items = []

    if isinstance(data, list):
        # could be a list of annotations or a list of doc blocks
        if data and isinstance(data[0], dict) and "matches" in data[0]:
            # list of {"doc":..., "matches": [...]} objects
            for block in data:
                doc = block.get("doc", "")
                for m in block.get("matches", []):
                    items.append(dict(m, doc=m.get("doc", doc)))
        else:
            items = data
    elif isinstance(data, dict):
        # formats like {"doc":..., "matches": [...]} are also supported
        matches = data.get("matches")
        if isinstance(matches, list):
            doc = data.get("doc", "")
            # propagate doc to matches if missing
            items = [dict(m, doc=m.get("doc", doc)) for m in matches]
        else:
            # single annotation object
            items = [data]

    res = set()
    for a in items:
        res.add((a.get("doc", ""), a["start"], a["end"], a["uri"]))
    return res


def load_ann(path):
    """Load annotations from a directory or a single file."""
    path = Path(path)
    if path.exists():
        files = [path] if path.is_file() else list(path.glob("*.json"))
    else:
        alt = path.with_suffix(".json")
        if alt.exists():
            files = [alt]
        else:
            raise FileNotFoundError(path)

    res = set()
    for fp in files:
        res.update(_load_file(fp))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pred_dir")
    ap.add_argument("gold_dir")
    args = ap.parse_args()

    pred = load_ann(args.pred_dir)
    gold = load_ann(args.gold_dir)

    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)

    prec = tp / (tp + fp) if tp+fp else 0
    rec  = tp / (tp + fn) if tp+fn else 0
    f1   = 2 * prec * rec / (prec + rec) if prec+rec else 0

    print(f"TP={tp} FP={fp} FN={fn}")
    print(f"Precision: {prec:.2%}  Recall: {rec:.2%}  F1: {f1:.2%}")

if __name__ == "__main__":
    main()
