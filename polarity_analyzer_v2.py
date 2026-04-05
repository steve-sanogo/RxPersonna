"""
polarity_analyzer_v2.py
=======================
Polarité ternaire symbolique calculée par chapitre.

Approche par PHRASE (et non par SVO strict) :
- Pour chaque phrase du chapitre, on identifie les personnages présents
  et les verbes polarisés (LEX_AMI / LEX_ENNEMI).
- Si une phrase contient au moins un verbe polarisé ET au moins deux
  personnages distincts, le signal du verbe est attribué à toutes
  les paires de personnages de cette phrase.
- La décision finale par paire est un vote majoritaire simple.

Cette approche est plus robuste que le parsing SVO strict car :
- le parsing en dépendances de SpaCy sur du narratif français rate
  souvent les liens sujet-objet (anaphores, inversions, ellipses)
- la co-présence dans une même phrase avec un verbe polarisé reste
  un signal interprétable et défendable académiquement

Note : l'ancienne méthode (PolarityAnalyzer dans polarity_analyzer.py)
est conservée comme perspective d'évolution méthodologique.
"""

from collections import defaultdict
from itertools import combinations


class ChapterPolarityAnalyzer:
    """
    Analyseur de polarité ternaire (ami / neutre / ennemi)
    basé sur les champs sémantiques de verbes, calculé par chapitre.
    """

    def __init__(self, corpus_type, resources):
        self.corpus_type = corpus_type
        self.res = resources

        # Ensembles de lemmes pour lookup rapide
        self.lex_ami = set(v.lower() for v in resources.get('LEX_AMI', []))
        self.lex_ennemi = set(v.lower() for v in resources.get('LEX_ENNEMI', []))
        self.negation_tokens = set(resources.get('NEGATION_TOKENS', []))

    def _find_characters_in_span(self, tokens, alias_map):
        """
        Identifie tous les personnages mentionnés dans une séquence de tokens.
        Retourne un set d'IDs canoniques.
        """
        found = set()
        for token in tokens:
            text_low = token.text.lower()
            for char_id, aliases in alias_map.items():
                if any(text_low == a.lower() for a in aliases):
                    found.add(char_id)
        return found

    def _classify_verb(self, verb_token):
        """
        Classifie un verbe : +1 (ami), -1 (ennemi), 0 (neutre).
        Gère l'inversion par négation.
        """
        lemma = verb_token.lemma_.lower()

        # Détection de négation
        negated = any(
            child.dep_ in ("advmod", "neg") and child.lemma_.lower() in self.negation_tokens
            for child in verb_token.children
        )

        if lemma in self.lex_ami:
            return -1 if negated else +1
        elif lemma in self.lex_ennemi:
            return +1 if negated else -1
        return 0

    def _get_sentence_signal(self, sent):
        """
        Analyse une phrase et retourne le signal dominant.
        Parcourt tous les verbes de la phrase, accumule +1/-1,
        et retourne le signal net.
        """
        signal = 0
        for token in sent:
            if token.pos_ == "VERB":
                s = self._classify_verb(token)
                signal += s
        return signal

    def analyze_chapter(self, doc, alias_groups, cooccurrences):
        """
        Analyse la polarité par phrase : pour chaque phrase contenant
        un verbe polarisé et 2+ personnages, on attribue le signal
        à toutes les paires de personnages de la phrase.

        Returns:
            dict { (charA, charB): score } compatible avec graph_builder
        """
        alias_map = {g[0]: g for g in alias_groups}

        # Compteurs par paire
        pair_signals = defaultdict(lambda: {"ami": 0, "ennemi": 0})

        for sent in doc.sents:
            # 1. Signal verbal de la phrase
            signal = self._get_sentence_signal(sent)
            if signal == 0:
                continue

            # 2. Personnages présents dans la phrase
            chars_in_sent = self._find_characters_in_span(sent, alias_map)
            if len(chars_in_sent) < 2:
                continue

            # 3. Attribution du signal à toutes les paires
            for char_a, char_b in combinations(sorted(chars_in_sent), 2):
                pair = tuple(sorted((char_a, char_b)))
                if signal > 0:
                    pair_signals[pair]["ami"] += 1
                else:
                    pair_signals[pair]["ennemi"] += 1

        # Vote majoritaire par paire
        polarity_map = {}
        for pair, counts in pair_signals.items():
            n_ami = counts["ami"]
            n_ennemi = counts["ennemi"]

            if n_ami > n_ennemi:
                polarity_map[pair] = float(n_ami - n_ennemi)
            elif n_ennemi > n_ami:
                polarity_map[pair] = -float(n_ennemi - n_ami)
            # Égalité → neutre (score 0, absent de la map)

        return polarity_map
