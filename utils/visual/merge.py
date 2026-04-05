import csv
import json
import re
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "outputs",
    "submission_finale_with_polarity_chapter_3labels_ctx_gd.csv"
)

data = {}

with open(INPUT_FILE, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        row_id   = row[0]            # ex: "lca0", "paf3"
        graphml  = row[1]            # contenu GraphML

        prefix = re.match(r'^([a-z]+)', row_id).group(1)   # "lca" ou "paf"
        num    = re.match(r'[a-z]+(\d+)', row_id).group(1) # "0", "3", ...

        if prefix not in data:
            data[prefix] = {}
        data[prefix][num] = graphml

# Sérialisation JSON compacte (sans espaces superflus)
json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# Ligne prête à coller dans le HTML
js_line = f"const GRAPH_DATA = {json_str};"

print(js_line[:120], "...")   # aperçu tronqué dans le terminal

# Écriture dans un fichier texte pour un copier-coller facile
with open("graph_data_js.txt", "w", encoding="utf-8") as out:
    out.write(js_line)

print("\n Contenu écrit dans graph_data_js.txt")
print(f"    Taille : {len(js_line):,} caractères")