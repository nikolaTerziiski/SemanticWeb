#!/usr/bin/env python3
import json
from pathlib import Path

def load_baseline(path):
    data = json.load(open(path, encoding="utf-8"))
    # ако файлът е обект с ключ "matches", ползваме него
    matches = data.get("matches", data) if isinstance(data, dict) else data
    return set((m["start"], m["end"], m["uri"]) for m in matches)

def load_gold(path):
    raw = json.load(open(path, encoding="utf-8"))
    gold_matches = []
    if isinstance(raw, list):
        # всеки елемент трябва да е { "doc":..., "matches":[...] }
        for entry in raw:
            gold_matches.extend(entry.get("matches", []))
    elif isinstance(raw, dict) and "matches" in raw:
        gold_matches = raw["matches"]
    else:
        raise ValueError("Неочакван формат на gold.json")
    return set((m["start"], m["end"], m["uri"]) for m in gold_matches)

if __name__ == "__main__":
    # Пример: сравняваме само Barolo.json
    baseline = load_baseline("output/Barolo.json")
    gold     = load_gold("resources/gold.json")

    tp = len(baseline & gold)
    fp = len(baseline - gold)
    fn = len(gold - baseline)

    precision = tp / (tp + fp) if tp+fp else 0.0
    recall    = tp / (tp + fn) if tp+fn else 0.0
    f1        = 2 * precision * recall / (precision + recall) if precision+recall else 0.0

    print(f"True Positives : {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}\n")
    print(f"Precision = {precision:.2f}")
    print(f"Recall    = {recall:.2f}")
    print(f"F1-score  = {f1:.2f}")
