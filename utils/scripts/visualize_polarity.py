import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import os
import xml.etree.ElementTree as ET

# Racine du projet (adapter le nombre de dirname selon l'emplacement du script)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))

CSV_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "outputs",
    "submission_finale_with_polarity_chapter_3labels_ctx_gd.csv"
)

IMAGES_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "images",
    "final"
)

# Map de couleurs pour les labels de polarité
POLARITY_COLORS = {
    "ami":     "#27ae60",   # Vert
    "neutre":  "#bdc3c7",   # Gris
    "ennemi":  "#c0392b"    # Rouge
}

# ---------------------

def get_clean_label(names_str, node_id):
    if not names_str: return node_id
    aliases = names_str.split(';')
    # Priorité aux noms canoniques
    PRIORITY = ["Hari Seldon", "Dors Venabili", "R. Daneel", "Cléon Ier", "Yugo Amaryl"]
    for p in PRIORITY:
        for a in aliases:
            if a.lower() == p.lower(): return p
    # Sinon le plus long sans bruits
    clean = [a.strip(" >-—.,") for a in aliases if len(a.strip()) > 1]
    return sorted(clean, key=len, reverse=True)[0] if clean else node_id


def load_graph_from_xml(xml_data):
    try:
        root = ET.fromstring(xml_data)
        ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
        G = nx.Graph()

        # 1. Mapping dynamique des clés (d0, d1, d2...)
        key_map = {}
        for key in root.findall(".//g:key", ns):
            key_map[key.get("id")] = key.get("attr.name")

        # 2. Chargement des Noeuds
        for node in root.findall(".//g:node", ns):
            node_id = node.get("id")
            name_val = node_id
            data = node.find(f".//g:data", ns)  # d0 par défaut pour les noms
            if data is not None: name_val = data.text
            G.add_node(node_id, label=get_clean_label(name_val, node_id))

        # 3. Chargement des Arêtes avec Attributs
        for edge in root.findall(".//g:edge", ns):
            source = edge.get("source")
            target = edge.get("target")
            edge_data = {"weight": 1, "polarity_label": "neutre", "polarity_score": 0.0}

            for data in edge.findall("g:data", ns):
                attr_name = key_map.get(data.get("key"))
                if attr_name in edge_data:
                    val = data.text
                    edge_data[attr_name] = float(val) if "score" in attr_name or "weight" in attr_name else val

            G.add_edge(source, target, **edge_data)

        return G
    except Exception as e:
        print(f"Erreur parsing: {e}")
        return nx.Graph()


def visualize_polarity_graph(G, title, save_path=None, layout="spring", highlight_node=None):
    plt.figure(figsize=(16, 12))

    # Choix du Layout
    if layout == "kamada":
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, k=0.5, iterations=50)

    # --- LOGIQUE VISUELLE DES ARÊTES ---
    edges = G.edges(data=True)
    # Couleurs basées sur le label
    edge_colors = [POLARITY_COLORS.get(d.get('polarity_label', 'neutre'), '#bdc3c7') for _, _, d in edges]
    # Épaisseur basée sur le poids (weight)
    edge_widths = [max(1, d.get('weight', 1) / 2) for _, _, d in edges]

    # --- LOGIQUE VISUELLE DES NOEUDS ---
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if highlight_node and node == highlight_node:
            node_colors.append('#2c3e50')  # Sombre pour le focus
            node_sizes.append(2000)
        else:
            node_colors.append('#ecf0f1')
            node_sizes.append(600)

    # Dessin des éléments
    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors, alpha=0.6)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors='#34495e', linewidths=1)

    # Labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold',
                            bbox=dict(facecolor="white", edgecolor='none', alpha=0.7, pad=0.2))

    plt.title(title, fontsize=20, pad=20)
    plt.axis('off')

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Visualisation sauvegardée : {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="ID chapitre (ex: lca3) ou 'all'")
    parser.add_argument("--ego", help="Nom du personnage central")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--layout", default="spring")
    args = parser.parse_args()

    # Chargement CSV
    df = pd.read_csv(CSV_PATH)

    if args.target.lower() == "all":
        full_G = nx.Graph()
        for _, row in df.iterrows():
            sub_G = load_graph_from_xml(row['graphml'])
            full_G = nx.compose(full_G, sub_G)
        final_G = full_G
        title = "Réseau Global - Polarité Relationnelle"
    else:
        row = df[df['ID'] == args.target]
        if row.empty: return
        final_G = load_graph_from_xml(row.iloc[0]['graphml'])
        title = f"Chapitre {args.target} - Polarité"

    target_id = None
    if args.ego:
        search = args.ego.lower()
        for node, data in final_G.nodes(data=True):
            if search in str(node).lower() or search in data['label'].lower():
                target_id = node
                break

        if target_id:
            final_G = nx.ego_graph(final_G, target_id, radius=1)
            title += f" (Focus: {final_G.nodes[target_id]['label']})"
        else:
            print(f"'{args.ego}' non trouvé.")
            return

    save_name = f"polarity_{args.target}_{args.ego if args.ego else ''}.png"
    save_path = os.path.join(IMAGES_PATH, save_name) if args.save else None

    visualize_polarity_graph(final_G, title, save_path, args.layout, highlight_node=target_id)


if __name__ == "__main__":
    main()