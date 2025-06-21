#!/usr/bin/env python3
import csv, json, re
from pathlib import Path

# --- Пътища ---
ROOT   = Path(__file__).resolve().parent.parent
DICT   = ROOT / "resources" / "surface_forms.csv"
CORPUS = ROOT / "corpus"
OUT    = ROOT / "output"
OUT.mkdir(exist_ok=True)

# --- 1. Зареждане на речника ---
def load_dictionary(path):
    d = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # пропускаме header
        for form, uri in reader:
            key = form.strip().lower()
            d.setdefault(key, []).append(uri.strip())
    return d

surface_dict = load_dictionary(DICT)
print(f"🔹 Loaded {len(surface_dict)} surface forms")

# --- 2. Обхождане на документите и търсене ---
for txt_path in CORPUS.glob("*.txt"):
    text = txt_path.read_text(encoding="utf-8")
    matches = []
    for form, uris in surface_dict.items():
        # търсим само цели думи
        pattern = rf"\b{re.escape(form)}\b"
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            for uri in uris:
                matches.append({
                    "start": m.start(),
                    "end":   m.end(),
                    "surface": m.group(0),
                    "uri": uri
                })
    # 3. Записваме резултатите в JSON
    out_file = OUT / f"{txt_path.stem}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump({
            "doc": txt_path.name,
            "matches": matches
        }, f, ensure_ascii=False, indent=2)
    print(f"{txt_path.name}: {len(matches)} matches")

print("✅ Matcher finished. Check output/*.json")