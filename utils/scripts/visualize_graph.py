import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import os
import xml.etree.ElementTree as ET
import re

# --- CONFIGURATION ---
CSV_PATH = "data/outputs/submission_finale_with_polarity_chapter_3labels_ctx_gd.csv"
IMAGES_PATH = "data/images/final"


# ---------------------

def get_clean_label(names_str, node_id):
    """
    Nettoie et choisit le meilleur nom pour l'affichage.
    Corrige spécifiquement les artefacts comme '>Seldon sourit'.
    """
    if not names_str:
        return node_id

    aliases = names_str.split(';')
    cleaned_aliases = []

    # 1. Nettoyage de base
    for alias in aliases:
        # Enlève les caractères parasites au début (> - —) et espaces
        clean = alias.strip(" >-—.,")
        if len(clean) > 1:
            cleaned_aliases.append(clean)

    if not cleaned_aliases:
        return node_id.strip(" >-—")

    # 2. RÈGLE D'OR : Si le nom complet canonique est dans la liste, on le prend direct !
    # Tu peux ajouter d'autres noms ici si besoin
    PRIORITY_NAMES = ["Hari Seldon", "Dors Venabili", "R. Daneel", "Cléon Ier", "Yugo Amaryl"]

    for priority in PRIORITY_NAMES:
        # Si on trouve un match exact (insensible à la casse), on le renvoie
        for alias in cleaned_aliases:
            if alias.lower() == priority.lower():
                return priority

    # 3. Stratégie de tri intelligente
    def score_name(name):
        score = 0

        # Bonus longueur (mais pas trop, pour éviter les phrases)
        score += len(name)

        # Gros Bonus si Majuscule au début
        if name[0].isupper():
            score += 20

        # Gros Malus si contient des indicateurs de bruit (verbes, >, etc)
        # Si ça ressemble à une phrase (contient "sourit", "dit", "répondit")
        noise_words = ["sourit", "dit", "répondit", "cria", "fit", "demand"]
        if any(w in name.lower() for w in noise_words):
            score -= 50

        # Malus si commence par un caractère spécial (bien que déjà nettoyé)
        if not name[0].isalnum():
            score -= 50

        return score

    # On trie par score décroissant
    best_name = sorted(cleaned_aliases, key=score_name, reverse=True)[0]
    return best_name


def load_graph_from_xml(xml_data):
    try:
        root = ET.fromstring(xml_data)
        ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
        G = nx.Graph()

        for node in root.findall(".//g:node", ns):
            node_id = node.get("id")
            data_names = node.find(".//g:data[@key='d0']", ns)
            names_str = data_names.text if data_names is not None else node_id

            # --- UTILISATION DE LA NOUVELLE FONCTION DE NETTOYAGE ---
            label = get_clean_label(names_str, node_id)
            # --------------------------------------------------------

            G.add_node(node_id, label=label)

        for edge in root.findall(".//g:edge", ns):
            G.add_edge(edge.get("source"), edge.get("target"))

        return G
    except Exception as e:
        return nx.Graph()


def visualize_graph(G, title, save_path=None, layout="spring", highlight_node=None):
    plt.figure(figsize=(14, 12))

    # Layout
    if layout == "spring":
        pos = nx.spring_layout(G, k=0.4, iterations=50)
    elif layout == "kamada":
        try:
            pos = nx.kamada_kawai_layout(G)
        except:
            pos = nx.spring_layout(G)
    else:
        pos = nx.circular_layout(G)

    # Couleurs
    node_colors = []
    node_sizes = []
    COLOR_DEFAULT = '#A0CBE2'
    COLOR_TARGET = '#FF4500'  # Orange/Rouge vif

    # Feedback console
    if highlight_node:
        label_target = G.nodes[highlight_node]['label']
        print(f"Focus visuel sur : '{label_target}' (ID: {highlight_node})")

    for node in G.nodes():
        if highlight_node and node == highlight_node:
            node_colors.append(COLOR_TARGET)
            node_sizes.append(1800)  # Encore plus gros pour la démo
        else:
            node_colors.append(COLOR_DEFAULT)
            node_sizes.append(400)

    # Dessin
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.95, edgecolors='white',
                           linewidths=1.5)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.4, edge_color='gray')

    # Labels avec fond blanc pour lisibilité parfaite
    labels = nx.get_node_attributes(G, 'label')

    # On dessine les labels
    # Astuce : On décale un peu le texte pour qu'il ne soit pas SOUS le point rouge
    text_pos = {k: (v[0], v[1] + 0.04) for k, v in pos.items()}

    nx.draw_networkx_labels(G, text_pos, labels, font_size=8, font_color='black', font_weight='bold',
                            bbox=dict(facecolor="white", edgecolor='none', alpha=0.7, pad=0.5))

    plt.title(title, fontsize=16, fontweight='bold')
    plt.axis('off')

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Image sauvegardée : {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="ID chapitre ou 'all'")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--layout", default="spring")
    parser.add_argument("--ego", type=str, help="Nom à chercher")
    args = parser.parse_args()

    # 1. Chargement
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        print(f"Erreur : {CSV_PATH} introuvable.")
        return

    # 2. Construction Graphe
    if args.target.lower() == "all":
        print("Fusion complète...")
        full_G = nx.Graph()
        for _, row in df.iterrows():
            sub_G = load_graph_from_xml(row['graphml'])
            full_G = nx.compose(full_G, sub_G)
        final_G = full_G
        base_title = "Graphe Complet"
        save_name = "graph_all"
    else:
        row = df[df['ID'] == args.target]
        if row.empty: return
        final_G = load_graph_from_xml(row.iloc[0]['graphml'])
        base_title = f"Chapitre {args.target}"
        save_name = f"graph_{args.target}"

    # 3. RECHERCHE INTELLIGENTE DU NOEUD
    target_node_id = None

    if args.ego:
        search_term = args.ego.lower()
        candidates = []

        # Recherche sur ID et sur LABEL
        for node, data in final_G.nodes(data=True):
            node_id_str = str(node).lower()
            label_str = str(data.get('label', '')).lower()

            if (search_term in node_id_str) or (node_id_str in search_term) or \
                    (search_term in label_str) or (label_str in search_term):
                candidates.append(node)

        if candidates:
            # On privilégie l'ID exact s'il existe (ex: 'Hari')
            candidates.sort(key=len)  # Le plus court est souvent l'ID racine
            target_node_id = candidates[0]

            # Ego Graph
            final_G = nx.ego_graph(final_G, target_node_id, radius=1)

            # Titre joli avec le Label nettoyé
            clean_label = final_G.nodes[target_node_id]['label']
            base_title += f" - Ego : {clean_label}"
            save_name += f"_EGO_{clean_label.replace(' ', '_')}"
        else:
            print(f"Personnage '{args.ego}' introuvable.")
            return

            # 4. Visualisation
    print(f"Affichage de {len(final_G)} nœuds.")
    save_path = os.path.join(IMAGES_PATH, save_name + ".png") if args.save else None

    visualize_graph(final_G, base_title, save_path, args.layout, highlight_node=target_node_id)


if __name__ == "__main__":
    main()


