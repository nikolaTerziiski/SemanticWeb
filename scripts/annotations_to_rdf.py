#!/usr/bin/env python3
"""Convert matcher output to RDF and load it into GraphDB.

This version does not rely on external libraries so it can run in a
restricted environment. It builds a small Turtle document manually and
POSTs it to the GraphDB Graph Store endpoint using ``urllib``.
"""

import json
import uuid
from pathlib import Path
from urllib import request

# --- Настройки ---
ROOT = Path(__file__).resolve().parent.parent
IN_JSON = ROOT / "output"           # папката с matcher_exact резултатите
ENDPOINT = "http://localhost:7200/repositories/WineRepo/statements"

# Namespace prefixes
TTL_HEADER = (
    "@prefix oa: <http://www.w3.org/ns/oa#> .\n"
    "@prefix ex: <http://example.org/ann#> .\n\n"
)

ttl_lines = [TTL_HEADER]
triple_count = 0

# 1) Прочитаме всеки JSON
for js in IN_JSON.glob("*.json"):
    data = json.loads(js.read_text(encoding="utf-8"))
    doc = data["doc"]
    for m in data["matches"]:
        ann = f"ex:{uuid.uuid4()}"
        tgt = f"ex:{uuid.uuid4()}"
        ttl_lines.extend(
            [
                f"{ann} a oa:Annotation ;",
                f"    oa:hasBody <{m['uri']}> ;",
                f"    oa:hasTarget {tgt} .",
                "",
                f"{tgt} a oa:TextPositionSelector ;",
                f"    oa:hasSource {json.dumps(doc)} ;",
                f"    oa:start {m['start']} ;",
                f"    oa:end {m['end']} .",
                "",
            ]
        )
        triple_count += 7

ttl_data = "\n".join(ttl_lines)
print(f"Генерирани са {triple_count} тройки; зареждаме в GraphDB…")

# 2) Публикуваме в GraphDB
req = request.Request(
    ENDPOINT,
    data=ttl_data.encode("utf-8"),
    headers={"Content-Type": "text/turtle"},
    method="POST",
)
with request.urlopen(req) as resp:
    resp.read()

print("✅ Успешно заредени анотациите в GraphDB.")
