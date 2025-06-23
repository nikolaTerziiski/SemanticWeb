# SemanticWeb
Project for the course Semantic Web in FMI

## Typical Workflow

Run the following steps to process a text file and evaluate the results:

1. Extract surface forms and build the FAISS index:
   ```bash
   python scripts/extract_surface_forms.py
   python scripts/build_index.py
   ```
2. Run the matcher on a document (e.g. `corpus/Barolo.txt`):
   ```bash
   python scripts/matcher_llm.py corpus/Barolo.txt
   ```
3. Evaluate the predictions against the gold annotations:
   ```bash
   python evaluate.py output resources/gold.json
   ```

`evaluate.py` accepts either a directory of JSON files or a single JSON
file for both the predictions and the gold annotations.
