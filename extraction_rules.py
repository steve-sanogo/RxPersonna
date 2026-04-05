class ExtractionRules:
    @staticmethod
    def apply_negation(score, is_negated, corpus_type):
        return score * -1.0 if is_negated else score

    @staticmethod
    def apply_modal(score, has_modal, corpus_type):
        return score * 0.5 if has_modal else score

    @staticmethod
    def apply_intensifier(score, has_intensifier, corpus_type):
        if not has_intensifier or score == 0:
            return score
        
        if corpus_type == "lca":
            return score * 1.5
        
        elif corpus_type == "paf":
            # Règle PAF : +1 à la valeur absolue, max 4
            if score > 0:
                return min(4.0, score + 1.0)
            else:
                return max(-4.0, score - 1.0)
        return score

    @staticmethod
    def get_label(score):
        """Labellisation legacy à 5 classes (conservée pour rétrocompatibilité)."""
        if score <= -1.5: return "ennemi"
        if score <= -0.5: return "plutot_ennemi"
        if score < 0.5:   return "neutre"
        if score < 1.5:   return "plutot_ami"
        return "ami"

    @staticmethod
    def get_label_3(score):
        """Labellisation ternaire : ami / neutre / ennemi (méthode principale)."""
        if score > 0:
            return "ami"
        elif score < 0:
            return "ennemi"
        return "neutre"