#!/usr/bin/env python3
"""
evaluate.py   pred_dir/   gold_dir/
Сравнява предсказаните и златните анотации, връща P / R / F1.
"""

import argparse, json
from pathlib import Path

def load_ann(path):
    res = set()
    for fp in Path(path).glob("*.json"):
        for a in json.load(fp.open(encoding="utf-8")):
            res.add((a["doc"], a["start"], a["end"], a["uri"]))
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
