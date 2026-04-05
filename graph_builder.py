import networkx as nx
import pandas as pd
from config import Config
from collections import defaultdict
from extraction_rules import ExtractionRules
import os


class GraphBuilder:
    def compute_cooccurrences(self, corpus_phrases, liste_alias, window_size=Config.WINDOW_SIZE):
        """
        Calcule les co-occurrences entre personnages dans une fenêtre glissante.
        """
        cooccurrences = defaultdict(int)

        # Fusionner tout le texte nettoyé
        full_text = " ".join([p for p in corpus_phrases if len(p) > Config.MIN_SENTENCE_LENGTH])
        tokens = full_text.split()

        # Préparer les patterns pour chaque groupe de personnages
        alias_patterns = {}
        for groupe in liste_alias:
            principal = groupe[0]
            alias_patterns[principal] = []
            for alias in groupe:
                alias_words = alias.lower().split()
                alias_patterns[principal].append(alias_words)

        # Identifier toutes les positions de chaque personnage dans le texte
        positions = defaultdict(list)
        for principal, patterns in alias_patterns.items():
            for pattern in patterns:
                for i in range(len(tokens) - len(pattern) + 1):
                    match = True
                    for j, word in enumerate(pattern):
                        token_clean = tokens[i + j].lower().strip('.,!?;:\"\'')
                        if token_clean != word:
                            match = False
                            break
                    if match:
                        positions[principal].append(i)

        # Calculer les liens selon la fenêtre de proximité
        personnages = list(positions.keys())
        for i, perso1 in enumerate(personnages):
            for j, perso2 in enumerate(personnages):
                if i >= j: continue
                count = 0
                for pos1 in positions[perso1]:
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
        """
        Choisit et formate les meilleurs noms (labels) pour l'export GraphML.
        """
        unique_names = list(set(alias_list))

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

    def create_submission_exact(self, alias_groups, cooccurrences, book, chapter, polarity_map=None):
        """
        Génère le graphe final avec nœuds, arêtes, poids et polarité.
        """
        G = nx.Graph()

        # --- 1. CRÉATION DES NŒUDS ---
        # Sans cette étape, le graphe reste vide et les arêtes ne peuvent pas être liées.
        for group in alias_groups:
            if group:
                principal = group[0]
                # On génère la liste des alias pour l'attribut 'names' du GraphML
                labels = GraphBuilder.clean_names_for_submission(group)
                G.add_node(principal, names=labels)

        # --- 2. CRÉATION DES ARÊTES ---
        for (char1, char2), weight in cooccurrences.items():
            # Sécurité : on vérifie que les nœuds ont bien été créés
            if weight > 0 and char1 in G.nodes and char2 in G.nodes:
                attrs = {"weight": weight}

                # Intégration de la polarité si le dictionnaire est fourni
                if polarity_map is not None:
                    pair = tuple(sorted((char1, char2)))
                    score = polarity_map.get(pair, 0.0)
                    attrs["polarity_score"] = round(score, 2)
                    # Labellisation selon la méthode configurée
                    if Config.POLARITY_METHOD == "chapter_3labels":
                        attrs["polarity_label"] = ExtractionRules.get_label_3(score)
                    else:
                        attrs["polarity_label"] = ExtractionRules.get_label(score)

                G.add_edge(char1, char2, **attrs)

        # --- 2b. SUPPRESSION DES NŒUDS ISOLÉS (FIX B) ---
        # Un nœud de degré 0 n'a aucune co-occurrence détectée → bruit pur
        isolates = list(nx.isolates(G))
        if isolates:
            G.remove_nodes_from(isolates)

        # --- 3. GÉNÉRATION DU CONTENU ET EXPORT ---
        chapter_id = f"{book}{chapter}"
        graphml_content = "".join(nx.generate_graphml(G))

        submission_df = pd.DataFrame({
            "ID": [chapter_id],
            "graphml": [graphml_content]
        })

        # Sauvegarde locale organisée par livre/chapitre
        folder_path = f"{Config.OUTPUT_PATH}/{book}/chap-{chapter}"
        os.makedirs(folder_path, exist_ok=True)
        file_path = f"{folder_path}/submission_local.csv"

        submission_df.set_index("ID", inplace=True)
        submission_df.to_csv(file_path)
        submission_df = submission_df.reset_index()

        return G, submission_df