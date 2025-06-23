#!/usr/bin/env python3
"""
annotations_to_rdf.py  out.json  http://localhost:7200/repositories/WineRepo
Конвертира JSON анотации към OA RDF (Turtle) и POST-ва в GraphDB.
"""

import sys, json, datetime, requests, textwrap

if len(sys.argv) != 3:
    print("Usage: annotations_to_rdf.py predictions.json GRAPHDB_REPO_URL")
    sys.exit(1)

PRED_JSON, GDB = sys.argv[1], sys.argv[2]
data = json.load(open(PRED_JSON, encoding="utf-8"))
ts   = datetime.datetime.utcnow().isoformat()

ttl_chunks = []
for i, ann in enumerate(data):
    ttl_chunks.append(textwrap.dedent(f"""
      <ann_{i}> a <http://www.w3.org/ns/oa#Annotation> ;
        <http://www.w3.org/ns/oa#hasBody> <{ann['uri']}> ;
        <http://www.w3.org/ns/oa#hasTarget> [
            a <http://www.w3.org/ns/oa#SpecificResource> ;
            <http://www.w3.org/ns/oa#hasSource> "{ann['doc']}" ;
            <http://www.w3.org/ns/oa#hasSelector> [
                 a <http://www.w3.org/ns/oa#TextPositionSelector> ;
                 <http://www.w3.org/ns/oa#start> {ann['start']} ;
                 <http://www.w3.org/ns/oa#end>   {ann['end']}
            ]
        ] ;
        <http://purl.org/dc/terms/created> "{ts}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
    """).strip())

ttl_doc = "@prefix oa: <http://www.w3.org/ns/oa#> .\n" + "\n\n".join(ttl_chunks)

r = requests.post(f"{GDB}/statements", data=ttl_doc.encode("utf-8"),
                  headers={"Content-Type": "text/turtle"})
print(f"GraphDB response: {r.status_code} {r.text[:200]}")
