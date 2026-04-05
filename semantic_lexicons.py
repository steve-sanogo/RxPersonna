"""
semantic_lexicons.py
====================
Lexiques sémantiques pour le filtrage contextuel des entités nommées.
Classifie verbes et adjectifs selon leur compatibilité avec la classe PERSONNE.

Utilisation : importé par context_entity_filter.py
"""


# ── VERBES TYPIQUEMENT ASSOCIÉS AUX PERSONNES ──────────────────────
# Actions humaines : communication, cognition, mouvement volontaire, émotion
HUMAN_VERBS = {
    # Communication / parole
    "parler", "dire", "répondre", "demander", "ordonner", "murmurer",
    "crier", "chuchoter", "annoncer", "déclarer", "expliquer", "raconter",
    "promettre", "menacer", "supplier", "implorer", "avouer", "mentir",
    "protester", "objecter", "rétorquer", "grommeler", "soupirer",
    "affirmer", "nier", "prétendre", "suggérer", "proposer", "insister",
    "répliquer", "confier", "bavarder", "discuter", "négocier",

    # Cognition / pensée
    "penser", "réfléchir", "croire", "douter", "comprendre", "savoir",
    "deviner", "imaginer", "supposer", "décider", "juger", "estimer",
    "hésiter", "se souvenir", "oublier", "planifier", "calculer",
    "soupçonner", "espérer", "craindre", "envisager", "conclure",

    # Mouvement volontaire
    "marcher", "courir", "entrer", "sortir", "se lever", "s'asseoir",
    "se retourner", "se diriger", "s'approcher", "reculer", "fuir",
    "suivre", "accompagner", "voyager", "revenir", "partir",

    # Émotion / réaction
    "sourire", "rire", "pleurer", "sursauter", "frémir", "trembler",
    "rougir", "pâlir", "grimacer", "froncer", "hocher", "secouer",
    "aimer", "détester", "haïr", "admirer", "mépriser", "envier",

    # Actions interpersonnelles
    "aider", "trahir", "combattre", "attaquer", "défendre", "protéger",
    "rencontrer", "saluer", "embrasser", "frapper", "tuer", "sauver",
    "obéir", "désobéir", "commander", "servir", "punir", "récompenser",
    "arrêter", "libérer", "recruter", "nommer", "exiler", "accuser",
}


# ── VERBES TYPIQUEMENT ASSOCIÉS AUX LIEUX / OBJETS / PLANÈTES ─────
# Phénomènes physiques, mouvements non-volontaires, propriétés spatiales
NON_HUMAN_VERBS = {
    # Astronomie / physique
    "orbiter", "tourner", "briller", "rayonner", "émettre", "absorber",
    "graviter", "pulser", "exploser", "imploser", "irradier", "s'effondrer",

    # Propriétés spatiales / géographiques
    "s'étendre", "s'élever", "surplomber", "dominer", "border",
    "entourer", "traverser", "longer", "séparer", "relier",

    # Propriétés d'objets / structures
    "fonctionner", "dysfonctionner", "rouiller", "craquer", "vibrer",
    "contenir", "renfermer", "mesurer", "peser", "résister",

    # Phénomènes naturels
    "pleuvoir", "neiger", "souffler", "gronder", "inonder",
}


# ── ADJECTIFS TYPIQUEMENT ASSOCIÉS AUX PERSONNES ──────────────────
# Traits de caractère, états émotionnels, qualités morales
HUMAN_ADJECTIVES = {
    # Traits de caractère
    "courageux", "lâche", "intelligent", "stupide", "rusé", "naïf",
    "prudent", "imprudent", "patient", "impatient", "honnête", "malhonnête",
    "loyal", "déloyal", "fidèle", "perfide", "ambitieux", "modeste",
    "arrogant", "humble", "cruel", "généreux", "avare", "égoïste",
    "altruiste", "cynique", "idéaliste", "pragmatique", "obstiné", "souple",

    # États émotionnels
    "inquiet", "anxieux", "calme", "furieux", "triste", "joyeux",
    "surpris", "étonné", "effrayé", "soulagé", "frustré", "satisfait",
    "mélancolique", "enthousiaste", "désespéré", "confiant", "nerveux",
    "perplexe", "pensif", "songeur", "méfiant", "soupçonneux",

    # Qualités physiques humaines
    "grand", "petit", "mince", "corpulent", "âgé", "jeune",
    "fatigué", "épuisé", "vigoureux", "malade", "blessé", "mort",
    "vivant", "conscient", "inconscient", "endormi", "éveillé",

    # Rôles sociaux (adjectivés)
    "puissant", "influent", "respecté", "craint", "aimé", "détesté",
    "célèbre", "inconnu", "riche", "pauvre", "noble", "savant",
}


# ── ADJECTIFS TYPIQUEMENT ASSOCIÉS AUX LIEUX / OBJETS / PLANÈTES ──
# Dimensions, propriétés physiques, qualités spatiales
NON_HUMAN_ADJECTIVES = {
    # Propriétés spatiales
    "vaste", "immense", "étroit", "large", "profond", "élevé",
    "lointain", "proche", "central", "périphérique", "souterrain",
    "continental", "planétaire", "galactique", "stellaire", "orbital",

    # Propriétés physiques
    "lumineux", "sombre", "brillant", "opaque", "transparent",
    "chaud", "froid", "glacial", "brûlant", "tempéré", "aride",
    "humide", "sec", "rocheux", "métallique", "gazeux",

    # Qualités d'environnement
    "désertique", "fertile", "stérile", "habitable", "inhabitable",
    "pollué", "toxique", "radioactif", "désolé", "peuplé",
    "industriel", "agricole", "urbain", "rural", "fortifié",

    # Propriétés d'objets
    "automatique", "mécanique", "électronique", "numérique",
    "ancien", "moderne", "obsolète", "fonctionnel", "défectueux",
}


class SemanticLexicons:
    """
    Accès centralisé aux lexiques sémantiques.
    Permet le calcul de scores de compatibilité PERSONNE.
    """

    def __init__(self):
        self.human_verbs = HUMAN_VERBS
        self.non_human_verbs = NON_HUMAN_VERBS
        self.human_adj = HUMAN_ADJECTIVES
        self.non_human_adj = NON_HUMAN_ADJECTIVES

    def score_verb(self, lemma):
        """Retourne +1 si verbe humain, -1 si non-humain, 0 si inconnu."""
        lemma_low = lemma.lower()
        if lemma_low in self.human_verbs:
            return 1.0
        if lemma_low in self.non_human_verbs:
            return -1.0
        return 0.0

    def score_adjective(self, lemma):
        """Retourne +1 si adjectif humain, -1 si non-humain, 0 si inconnu."""
        lemma_low = lemma.lower()
        if lemma_low in self.human_adj:
            return 1.0
        if lemma_low in self.non_human_adj:
            return -1.0
        return 0.0
