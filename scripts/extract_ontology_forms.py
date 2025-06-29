#!/usr/bin/env python3
"""
extract_ontology_forms.py

Parses the wine OWL ontology, extracts classes and individuals,
generates human-readable surface forms from their IDs, and saves
them to a CSV file in the resources directory.
"""
import csv
import re
from pathlib import Path
import sys

# Define ROOT and add to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from rdflib import Graph, RDFS, OWL
from rdflib.term import URIRef

# --- Configuration ---
ONTOLOGY_FILE = ROOT / "ontology" / "wine.rdf"
OUTPUT_CSV = ROOT / "resources" / "surface_forms.csv"
BASE_URI = "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine#"

def camel_case_split(identifier):
    """Splits a CamelCase identifier into words."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', identifier)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)

def main():
    """Main function to extract forms and write to CSV."""
    if not ONTOLOGY_FILE.exists():
        print(f"Error: Ontology file not found at {ONTOLOGY_FILE}")
        return

    g = Graph()
    print(f"Loading ontology from {ONTOLOGY_FILE}...")
    g.parse(str(ONTOLOGY_FILE))
    print(f"Ontology loaded. Found {len(g)} statements.")

    concepts = set()
    # Query for all OWL classes and individuals that are part of the wine namespace
    subjects = set(g.subjects(None, None))
    for s in subjects:
         if isinstance(s, URIRef) and str(s).startswith(BASE_URI):
            concepts.add(s)

    print(f"Found {len(concepts)} unique concepts (classes and individuals).")

    output_data = []
    for uri in sorted(list(concepts)):
        local_name = uri.fragment
        if not local_name:
            continue

        surface_form = camel_case_split(local_name).strip()

        if len(surface_form) > 2:
            output_data.append({"uri": str(uri), "form": surface_form})

        for label in g.objects(uri, RDFS.label):
            label_form = str(label).strip()
            if len(label_form) > 2:
                output_data.append({"uri": str(uri), "form": label_form})

    unique_output_data = [dict(t) for t in {tuple(d.items()) for d in output_data}]
    unique_output_data.sort(key=lambda x: x['form'])

    print(f"Writing {len(unique_output_data)} surface forms to {OUTPUT_CSV}...")
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["form", "uri"])
        writer.writeheader()
        writer.writerows(unique_output_data)

    print("✅ Done. Surface forms extracted successfully.")

if __name__ == "__main__":
    main()