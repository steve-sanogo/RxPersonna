"""
graph_disambiguation.py
=======================
Désambiguïsation des entités basée sur la structure du graphe.

Deux mécanismes complémentaires :

1. JACCARD STRUCTUREL
   Calcule la similarité entre deux nœuds en comparant leurs ensembles
   de voisins dans le graphe. Deux nœuds ayant des voisins très similaires
   sont probablement des alias du même personnage.

2. ANALYSE DU VOISINAGE
   Étudie la composition du voisinage local d'un nœud pour valider
   ou corriger sa classification. Un nœud PER isolé parmi des LOC
   est suspect.

Ce module s'applique APRÈS la construction du graphe initial.
Il produit des suggestions de fusion ou de correction, sans
modifier directement les groupes d'alias existants (approche non-destructive).
"""

import networkx as nx
from collections import defaultdict


class GraphDisambiguator:
    def __init__(self, similarity_threshold=None):
        """
        Args:
            similarity_threshold: seuil de Jaccard au-dessus duquel
                deux nœuds sont considérés comme potentiellement équivalents.
                Défaut : Config.GRAPH_DISAMBIG_THRESHOLD
        """
        from config import Config
        self.threshold = similarity_threshold or Config.GRAPH_DISAMBIG_THRESHOLD

    # ────────────────────────────────────────────────────────────────
    # 1. JACCARD STRUCTUREL
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def jaccard_neighbors(G, node_a, node_b):
        """
        Calcule le coefficient de Jaccard entre les ensembles de voisins
        de deux nœuds dans le graphe G.

        J(A,B) = |N(A) ∩ N(B)| / |N(A) ∪ N(B)|

        On exclut A et B eux-mêmes de leurs voisinages respectifs.

        Returns:
            float entre 0.0 et 1.0
        """
        if node_a not in G or node_b not in G:
            return 0.0

        neighbors_a = set(G.neighbors(node_a)) - {node_b}
        neighbors_b = set(G.neighbors(node_b)) - {node_a}

        if not neighbors_a and not neighbors_b:
            return 0.0

        intersection = neighbors_a & neighbors_b
        union = neighbors_a | neighbors_b

        return len(intersection) / len(union) if union else 0.0

    def find_merge_candidates(self, G, alias_groups=None):
        """
        Identifie les paires de nœuds ayant un Jaccard structurel élevé.
        Ce sont des candidats à la fusion (probables alias non détectés).

        Args:
            G: graphe NetworkX
            alias_groups: groupes d'alias existants (pour ne pas re-proposer
                des fusions déjà connues)

        Returns:
            liste de tuples (node_a, node_b, jaccard_score)
            triée par score décroissant
        """
        # Construire l'index des nœuds déjà dans le même groupe
        already_grouped = set()
        if alias_groups:
            for group in alias_groups:
                principal = group[0]
                for alias in group[1:]:
                    pair = tuple(sorted((principal, alias)))
                    already_grouped.add(pair)

        candidates = []
        nodes = list(G.nodes())

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_a, node_b = nodes[i], nodes[j]
                pair = tuple(sorted((node_a, node_b)))

                # Ignorer les paires déjà dans le même groupe d'alias
                if pair in already_grouped:
                    continue

                # Ignorer les nœuds directement connectés avec poids élevé
                # (ce sont déjà des relations confirmées, pas des alias)
                if G.has_edge(node_a, node_b):
                    continue

                score = self.jaccard_neighbors(G, node_a, node_b)

                if score >= self.threshold:
                    candidates.append((node_a, node_b, round(score, 3)))

        # Tri par score décroissant
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates

    # ────────────────────────────────────────────────────────────────
    # 2. ANALYSE DU VOISINAGE
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def analyze_node_neighborhood(G, node, entity_types=None):
        """
        Analyse la composition du voisinage d'un nœud.

        Args:
            G: graphe NetworkX
            node: identifiant du nœud
            entity_types: dict {node_id: 'PER'|'LOC'|'ORG'} si disponible

        Returns:
            dict avec métriques du voisinage :
            {
                'degree': int,
                'neighbors': list,
                'avg_weight': float,
                'neighbor_types': Counter (si entity_types fourni),
                'isolation_score': float (0=bien connecté, 1=isolé)
            }
        """
        if node not in G:
            return {'degree': 0, 'neighbors': [], 'avg_weight': 0.0,
                    'isolation_score': 1.0}

        neighbors = list(G.neighbors(node))
        degree = len(neighbors)

        # Poids moyen des arêtes
        weights = []
        for neighbor in neighbors:
            edge_data = G[node][neighbor]
            weights.append(edge_data.get('weight', 1))
        avg_weight = sum(weights) / len(weights) if weights else 0.0

        result = {
            'degree': degree,
            'neighbors': neighbors,
            'avg_weight': round(avg_weight, 2),
        }

        # Score d'isolation : basé sur le degré relatif dans le graphe
        max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1
        result['isolation_score'] = round(1.0 - (degree / max_degree), 3) if max_degree > 0 else 1.0

        # Analyse des types de voisins si disponible
        if entity_types:
            from collections import Counter
            neighbor_type_counts = Counter()
            for n in neighbors:
                n_type = entity_types.get(n, 'UNKNOWN')
                neighbor_type_counts[n_type] += 1
            result['neighbor_types'] = dict(neighbor_type_counts)

        return result

    def detect_suspicious_nodes(self, G, min_degree=1):
        """
        Détecte les nœuds structurellement suspects (potentiels faux positifs).

        Critères :
        - Degré très faible (isolé dans le réseau)
        - Connecté à un seul voisin avec poids = 1 (co-occurrence minimale)

        Args:
            G: graphe NetworkX
            min_degree: degré minimum pour ne pas être suspect

        Returns:
            liste de (node_id, raison) pour les nœuds suspects
        """
        suspicious = []

        for node in G.nodes():
            degree = G.degree(node)

            if degree == 0:
                suspicious.append((node, "isolé (degré 0)"))
                continue

            if degree <= min_degree:
                # Vérifier si la seule connexion est faible
                neighbors = list(G.neighbors(node))
                max_weight = max(
                    G[node][n].get('weight', 1) for n in neighbors
                )
                if max_weight <= 1:
                    suspicious.append((node, f"faiblement connecté (degré={degree}, poids_max={max_weight})"))

        return suspicious

    # ────────────────────────────────────────────────────────────────
    # 3. APPLICATION DES FUSIONS (optionnel, non-destructif)
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def apply_merge_to_groups(alias_groups, merge_candidates, max_merges=5):
        """
        Applique les fusions suggérées aux groupes d'alias existants.
        Version conservative : ne fusionne que les N meilleurs candidats.

        Args:
            alias_groups: liste de groupes d'alias existants
            merge_candidates: sortie de find_merge_candidates
            max_merges: nombre maximum de fusions à appliquer

        Returns:
            nouveaux alias_groups avec les fusions appliquées
        """
        if not merge_candidates:
            return alias_groups

        # Index inversé : nom → index du groupe
        name_to_group_idx = {}
        for idx, group in enumerate(alias_groups):
            for name in group:
                name_to_group_idx[name] = idx

        # Appliquer les fusions (les meilleurs candidats d'abord)
        merged_indices = set()  # Groupes déjà absorbés
        groups_copy = [list(g) for g in alias_groups]

        for node_a, node_b, score in merge_candidates[:max_merges]:
            idx_a = name_to_group_idx.get(node_a)
            idx_b = name_to_group_idx.get(node_b)

            if idx_a is None or idx_b is None:
                continue
            if idx_a == idx_b:
                continue  # Déjà dans le même groupe
            if idx_a in merged_indices or idx_b in merged_indices:
                continue

            # Fusionner B dans A
            groups_copy[idx_a].extend(
                n for n in groups_copy[idx_b] if n not in groups_copy[idx_a]
            )
            merged_indices.add(idx_b)

            # Mettre à jour l'index
            for name in groups_copy[idx_b]:
                name_to_group_idx[name] = idx_a

        # Reconstruire la liste sans les groupes absorbés
        return [g for i, g in enumerate(groups_copy) if i not in merged_indices]

    # ────────────────────────────────────────────────────────────────
    # 4. RAPPORT DE DIAGNOSTIC
    # ────────────────────────────────────────────────────────────────

    def generate_report(self, G, alias_groups=None, verbose=True):
        """
        Génère un rapport complet de désambiguïsation.

        Returns:
            dict avec les résultats d'analyse
        """
        report = {
            'merge_candidates': self.find_merge_candidates(G, alias_groups),
            'suspicious_nodes': self.detect_suspicious_nodes(G),
            'graph_stats': {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': round(nx.density(G), 4),
                'components': nx.number_connected_components(G),
            }
        }

        if verbose:
            mc = report['merge_candidates']
            sn = report['suspicious_nodes']
            print(f"   [GraphDisambig] Candidats fusion : {len(mc)}")
            for a, b, s in mc[:5]:  # Top 5
                print(f"      • {a} ↔ {b} (Jaccard={s})")
            print(f"   [GraphDisambig] Nœuds suspects : {len(sn)}")
            for node, reason in sn[:5]:
                print(f"      • {node} : {reason}")

        return report
