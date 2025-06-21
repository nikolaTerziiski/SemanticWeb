#!/usr/bin/env python3
import csv
from pathlib import Path
from rdflib import Graph, RDFS, Namespace

# --- Конфигурация на пътищата ---
ROOT      = Path(__file__).resolve().parent.parent
ONTO_PATH = ROOT / "ontology" / "wine" / "wine.rdf"
OUT_CSV   = ROOT / "resources" / "surface_forms.csv"

# --- Namespace за skos ---
SKOS      = Namespace("http://www.w3.org/2004/02/skos/core#")

# 1) Зареди онтологията
g = Graph()
g.parse(ONTO_PATH.resolve().as_uri(), format="xml")
 # ако е RDF/XML; ако е TTL – use format="ttl"

# 2) Събери всички form+URI
rows = []
for s, p, o in g.triples((None, RDFS.label, None)):
    # само английски или без език
    if o.language in (None, "", "en"):
        rows.append((str(o), str(s)))
for s, p, o in g.triples((None, SKOS.altLabel, None)):
    if o.language in (None, "", "en"):
        rows.append((str(o), str(s)))

# 3) Запиши CSV
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["form", "uri"])
    # премахваме дубли
    seen = set()
    for form, uri in rows:
        key = (form.lower(), uri)
        if key not in seen:
            writer.writerow([form, uri])
            seen.add(key)

print(f"✅ Written {len(seen)} surface forms to {OUT_CSV}")
