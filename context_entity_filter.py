"""
context_entity_filter.py
========================
Filtrage contextuel des entités nommées de type PERSONNE.

Pour chaque entité candidate, on analyse une fenêtre de contexte local
et on calcule un score de compatibilité avec la classe PERSONNE en se basant
sur les verbes et adjectifs environnants.

Score > 0  →  probable personnage (verbes/adjectifs humains dominants)
Score < 0  →  probable faux positif (lieu, objet, planète)
Score = 0  →  aucun signal contextuel, on conserve l'entité par défaut

Ce module s'insère APRÈS l'extraction NER et AVANT le vote / résolution d'alias.
Il ne remplace PAS la blacklist existante — il la complète.
"""

from semantic_lexicons import SemanticLexicons
from config import Config


class ContextEntityFilter:
    def __init__(self, nlp_model, lexicons=None):
        """
        Args:
            nlp_model: modèle SpaCy chargé (fr_core_news_md)
            lexicons: instance SemanticLexicons (créée par défaut si None)
        """
        self.nlp = nlp_model
        self.lex = lexicons or SemanticLexicons()

    def _find_entity_spans(self, doc, entity_text):
        """
        Localise toutes les occurrences d'une entité dans le doc SpaCy.
        Retourne une liste de positions (index du premier token).
        """
        entity_lower = entity_text.lower().split()
        positions = []
        tokens_lower = [t.text.lower() for t in doc]

        for i in range(len(tokens_lower) - len(entity_lower) + 1):
            if tokens_lower[i:i + len(entity_lower)] == entity_lower:
                positions.append(i)

        return positions

    def _extract_context_signals(self, doc, position, entity_length, window):
        """
        Extrait les verbes et adjectifs dans une fenêtre autour de l'entité.

        Args:
            doc: document SpaCy
            position: index du premier token de l'entité
            entity_length: nombre de tokens de l'entité
            window: taille de la fenêtre (en tokens, de chaque côté)

        Returns:
            dict avec listes de lemmes : {'verbs': [...], 'adjectives': [...]}
        """
        start = max(0, position - window)
        end = min(len(doc), position + entity_length + window)

        signals = {'verbs': [], 'adjectives': []}

        for i in range(start, end):
            # On ignore les tokens de l'entité elle-même
            if position <= i < position + entity_length:
                continue

            token = doc[i]

            if token.pos_ == "VERB":
                signals['verbs'].append(token.lemma_.lower())

            elif token.pos_ == "ADJ":
                signals['adjectives'].append(token.lemma_.lower())

        return signals

    def compute_person_score(self, doc, entity_text, window=None):
        """
        Calcule le score de compatibilité PERSONNE pour une entité donnée.

        Le score est la somme des contributions des verbes et adjectifs
        trouvés dans les fenêtres de contexte autour de chaque occurrence.

        Args:
            doc: document SpaCy du chapitre
            entity_text: texte de l'entité candidate
            window: taille de fenêtre (défaut: Config.CONTEXT_FILTER_WINDOW)

        Returns:
            float: score cumulé (positif = humain, négatif = non-humain)
        """
        if window is None:
            window = Config.CONTEXT_FILTER_WINDOW

        positions = self._find_entity_spans(doc, entity_text)

        if not positions:
            return 0.0  # Entité non retrouvée dans le texte → neutre

        total_score = 0.0
        total_signals = 0

        for pos in positions:
            entity_length = len(entity_text.split())
            signals = self._extract_context_signals(doc, pos, entity_length, window)

            for verb_lemma in signals['verbs']:
                s = self.lex.score_verb(verb_lemma)
                total_score += s
                if s != 0:
                    total_signals += 1

            for adj_lemma in signals['adjectives']:
                s = self.lex.score_adjective(adj_lemma)
                total_score += s * Config.CONTEXT_FILTER_ADJ_WEIGHT
                if s != 0:
                    total_signals += 1

        # Normalisation par le nombre d'occurrences pour éviter
        # qu'un personnage très mentionné ait un score artificiellement élevé
        if len(positions) > 1:
            total_score /= len(positions)

        return total_score

    def filter_entities(self, entities, corpus_filtered, verbose=False):
        """
        Filtre une liste d'entités extraites par NER en utilisant le contexte.

        Args:
            entities: liste de dicts [{'text': '...', 'type': 'PER'}, ...]
            corpus_filtered: liste de phrases (même corpus que celui du NER)
            verbose: si True, affiche les détails du filtrage

        Returns:
            liste d'entités filtrées (même format que l'entrée)
        """
        # On ne filtre que les PER, les LOC et ORG passent directement
        per_entities = [e for e in entities if e.get('type') == 'PER']
        other_entities = [e for e in entities if e.get('type') != 'PER']

        if not per_entities:
            return entities

        # Construire un seul doc SpaCy pour le chapitre (performance)
        full_text = " ".join(corpus_filtered)
        doc = self.nlp(full_text)

        # Calculer les scores pour chaque entité PER unique
        unique_texts = set(e['text'] for e in per_entities)
        scores = {}

        for ent_text in unique_texts:
            scores[ent_text] = self.compute_person_score(doc, ent_text)

        # Filtrage selon le seuil
        threshold = Config.CONTEXT_FILTER_THRESHOLD
        kept_per = []
        removed = []

        for ent in per_entities:
            score = scores.get(ent['text'], 0.0)

            # On ne filtre que si le score est franchement négatif
            # Score = 0 (aucun signal) → on garde par précaution
            if score < threshold:
                removed.append((ent['text'], score))
            else:
                kept_per.append(ent)

        if verbose and removed:
            print(f"   [ContextFilter] Entités filtrées ({len(removed)}) :")
            for name, sc in removed:
                print(f"      - '{name}' (score: {sc:.2f})")

        return kept_per + other_entities
