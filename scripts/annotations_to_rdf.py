#!/usr/bin/env python3
import json, uuid
from pathlib import Path
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from SPARQLWrapper import SPARQLWrapper, POST

# --- Настройки ---
ROOT = Path(__file__).resolve().parent.parent
IN_JSON = ROOT / "output"           # папката с matcher_exact резултатите
ENDPOINT = "http://localhost:7200/repositories/wine/statements"

# Namespaces
OA   = Namespace("http://www.w3.org/ns/oa#")
EX   = Namespace("http://example.org/ann#")

g = Graph()
g.bind("oa", OA)

# 1) Прочитаме всеки JSON
for js in IN_JSON.glob("*.json"):
    data = json.loads(js.read_text(encoding="utf-8"))
    doc  = data["doc"]
    for m in data["matches"]:
        ann = EX[str(uuid.uuid4())]
        # aнотация
        g.add((ann, RDF.type,        OA.Annotation))
        g.add((ann, OA.hasBody,       URIRef(m["uri"])))
        # таргет със selector
        tgt = EX[str(uuid.uuid4())]
        g.add((ann, OA.hasTarget,     tgt))
        g.add((tgt, RDF.type,         OA.TextPositionSelector))
        g.add((tgt, OA.hasSource,     Literal(doc)))
        g.add((tgt, OA.start,         Literal(m["start"])))
        g.add((tgt, OA.end,           Literal(m["end"])))

print(f"Генерирани са {len(g)} тройки; зареждаме в GraphDB…")

# 2) Публикуваме в GraphDB
sparql = SPARQLWrapper(ENDPOINT)
sparql.setMethod(POST)
sparql.setRequestMethod(POST)
sparql.setHeader("Content-Type", "text/turtle")
sparql.setBody(g.serialize(format="turtle"))
sparql.query()

print("✅ Успешно заредени анотациите в GraphDB.")
