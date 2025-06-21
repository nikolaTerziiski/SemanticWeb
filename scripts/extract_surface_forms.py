#!/usr/bin/env python3
import csv, re
from pathlib import Path
from rdflib import Graph, RDFS, Namespace, URIRef

# --- Настройки ---
ROOT      = Path(__file__).resolve().parent.parent
ONTO_PATH = ROOT / "ontology" / "wine.rdf"
OUT_CSV   = ROOT / "resources" / "surface_forms.csv"

SKOS      = Namespace("http://www.w3.org/2004/02/skos/core#")

# 1) Зареди RDF/XML
g = Graph()
g.parse(ONTO_PATH.resolve().as_uri(), format="xml")

# 2) Събери всички рdfs:label и skos:altLabel
entries = []
for s, p, o in g.triples((None, RDFS.label, None)):
    if o.language in (None, "", "en"):
        entries.append((str(o), str(s)))
for s, p, o in g.triples((None, SKOS.altLabel, None)):
    if o.language in (None, "", "en"):
        entries.append((str(o), str(s)))

# 3) Фолбек на URI local name за всеки ресурс в wine namespace
wine_ns = "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine#"
for s in set(s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(wine_ns)):
    uri = str(s)
    # ако вече нямаме entry за този URI
    if not any(uri == e[1] for e in entries):
        local = uri.split("#")[-1]
        # CamelCase -> "Camel Case"
        form = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", local)
        entries.append((form, uri))

# 4) Напиши CSV без дубли
seen = set()
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["form", "uri"])
    for form, uri in entries:
        key = (form.lower(), uri)
        if key not in seen:
            writer.writerow([form, uri])
            seen.add(key)

print(f"✅ Written {len(seen)} surface forms to {OUT_CSV}")
