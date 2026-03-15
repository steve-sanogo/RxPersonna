from collections import defaultdict
import re
from extraction_rules import ExtractionRules
from config import Config


class PolarityAnalyzer:
    def __init__(self, corpus_type, resources):
        self.corpus_type = corpus_type
        self.res = resources
        self.rules = ExtractionRules()

    def get_char_id(self, token_text, alias_map):
        """Identifie l'ID d'un personnage à partir d'un texte brut."""
        text_low = token_text.lower()
        for char_id, aliases in alias_map.items():
            if any(text_low == a.lower() for a in aliases):
                return char_id
        return None

    def calculate_event_score(self, verb_token):
        """Calcule s_e (score local) avec modulations linguistiques."""
        lemma = verb_token.lemma_.lower()
        base_score = self.res.get('LEX_SCORE', {}).get(lemma, 0.0)

        if base_score == 0: return 0.0

        # Analyse des modificateurs syntaxiques
        is_neg = any(t.dep_ == "neg" or t.lemma_ in self.res['NEGATION_TOKENS'] for t in verb_token.children)
        has_modal = any(t.lemma_ in self.res['MODALS'] for t in verb_token.children)
        has_intense = any(t.lemma_ in self.res['INTENSIFIERS'] for t in verb_token.children)

        score = self.rules.apply_negation(base_score, is_neg, self.corpus_type)
        score = self.rules.apply_modal(score, has_modal, self.corpus_type)
        score = self.rules.apply_intensifier(score, has_intense, self.corpus_type)

        return score

    def detect_affiliations(self, text, alias_map):
        """Détecte les liens de parenté ou d'alliance via patterns (Delta)."""
        affiliations = []
        for entry in self.res.get('AFFILIATION_PATTERNS', []):
            label = entry['label']
            hint = entry['polarity_hint']
            for pattern in entry['patterns']:
                # On cherche "Prénom1 pattern Prénom2"
                # Exemple : "Hari fils de Gaal"
                match = re.search(rf"(\w+)\s+{pattern}\s+(\w+)", text, re.IGNORECASE)
                if match:
                    char_a = self.get_char_id(match.group(1), alias_map)
                    char_b = self.get_char_id(match.group(2), alias_map)
                    if char_a and char_b and char_a != char_b:
                        affiliations.append((tuple(sorted((char_a, char_b))), hint))
        return affiliations

    def analyze_chapter(self, doc, alias_groups, cooccurrences):
        """
        Calcule S_c(A,B) = Σ actions + β Σ dialogues + δ Σ affiliations + ε f(cooc)
        """
        # Map inverse pour identification rapide
        alias_map = {g[0]: g for g in alias_groups}
        pair_scores = defaultdict(float)

        # 1. & 2. ANALYSE SVO (Actions & Dialogues avec Beta)
        for token in doc:
            if token.pos_ == "VERB":
                subj = next((t for t in token.children if "subj" in t.dep_), None)
                obj = next((t for t in token.children if t.dep_ in ("obj", "iobj", "obl")), None)

                if subj and obj:
                    id_s = self.get_char_id(subj.text, alias_map)
                    id_o = self.get_char_id(obj.text, alias_map)

                    if id_s and id_o and id_s != id_o:
                        pair = tuple(sorted((id_s, id_o)))
                        s_e = self.calculate_event_score(token)

                        # Si verbe de parole -> on applique Beta
                        if token.lemma_.lower() in self.res.get('SPEECH_VERBS', []):
                            pair_scores[pair] += s_e * Config.POLARITY_BETA
                        else:
                            pair_scores[pair] += s_e

        # 3. ANALYSE DES AFFILIATIONS (Delta)
        # On parcourt chaque phrase pour chercher les patterns d'affiliation
        for sent in doc.sents:
            affs = self.detect_affiliations(sent.text, alias_map)
            for pair, hint in affs:
                pair_scores[pair] += hint * Config.POLARITY_DELTA

        # 4. SIGNAL FAIBLE COOCCURRENCE (Epsilon)
        for (a, b), weight in cooccurrences.items():
            pair_scores[tuple(sorted((a, b)))] += weight * Config.POLARITY_EPSILON

        return pair_scores