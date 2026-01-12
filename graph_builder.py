import networkx as nx
import pandas as pd
from config import Config
from collections import defaultdict
import os


class GraphBuilder:
    def compute_cooccurrences(self, corpus_phrases, liste_alias, window_size=Config.WINDOW_SIZE):
        cooccurrences = defaultdict(int)

        # Fusionner tout le texte (Sécurité : on réapplique le filtre ici au cas où)
        full_text = " ".join([p for p in corpus_phrases if len(p) > Config.MIN_SENTENCE_LENGTH])
        tokens = full_text.split()

        # Préparer les patterns
        alias_patterns = {}
        for groupe in liste_alias:
            principal = groupe[0]
            alias_patterns[principal] = []
            for alias in groupe:
                # Pattern de matching flexible
                alias_words = alias.lower().split()
                alias_patterns[principal].append(alias_words)

        # Trouver toutes les positions
        positions = defaultdict(list)
        for principal, patterns in alias_patterns.items():
            for pattern in patterns:
                for i in range(len(tokens) - len(pattern) + 1):
                    # Vérifier le match
                    match = True
                    for j, word in enumerate(pattern):
                        # Nettoyage de la ponctuation collée aux mots pour la comparaison
                        token_clean = tokens[i + j].lower().strip('.,!?;:\"\'')
                        if token_clean != word:
                            match = False
                            break
                    if match:
                        positions[principal].append(i)

        # Compter les co-occurrences
        personnages = list(positions.keys())
        for i, perso1 in enumerate(personnages):
            for j, perso2 in enumerate(personnages):
                if i >= j:
                    continue

                count = 0
                for pos1 in positions[perso1]:
                    # Vérifier si perso2 est dans la fenêtre autour de pos1
                    for pos2 in positions[perso2]:
                        if pos1 != pos2 and abs(pos1 - pos2) <= window_size:
                            count += 1
                            break

                if count > 0:
                    pair = tuple(sorted([perso1, perso2]))
                    cooccurrences[pair] = count

        return cooccurrences

    @staticmethod
    def clean_names_for_submission(alias_list):
        # Stratégie "Best Name Only" pour maximiser la Précision
        unique_names = list(set(alias_list))

        # Tri : Plus long d'abord, Majuscules d'abord
        def sort_key(name):
            has_cap = any(c.isupper() for c in name)
            return (-len(name), not has_cap, name)

        sorted_candidates = sorted(unique_names, key=sort_key)

        final_names = []
        seen_lower = set()

        for name in sorted_candidates:
            low = name.lower()
            if low not in seen_lower:
                final_names.append(name)
                seen_lower.add(low)

        return ";".join(final_names)

    def create_submission_exact(self, alias_groups, cooccurrences, book, chapter):
        G = nx.Graph()

        for group in alias_groups:
            if group:
                principal = group[0]
                names = GraphBuilder.clean_names_for_submission(group)
                G.add_node(principal, names=names)

        for (char1, char2), weight in cooccurrences.items():
            if weight > 0 and char1 in G.nodes and char2 in G.nodes:
                G.add_edge(char1, char2)

        chapter_id = f"{book}{chapter}"
        graphml_content = "".join(nx.generate_graphml(G))

        submission_df = pd.DataFrame({
            "ID": [chapter_id],
            "graphml": [graphml_content]
        })

        # --- CORRECTION DU CHEMIN ---
        # On définit le dossier
        folder_path = f"{Config.OUTPUT_PATH}/{book}/chap-{chapter}"
        os.makedirs(folder_path, exist_ok=True)

        # On définit le fichier (ex: submission_chap_X.csv)
        file_path = f"{folder_path}/submission_local.csv"

        submission_df.set_index("ID", inplace=True)
        submission_df.to_csv(file_path)
        submission_df = submission_df.reset_index()  # Pour le return

        return G, submission_df