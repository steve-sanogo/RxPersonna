import os


class Config:
    # --- RACINE DU PROJET ---
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    # --- CHEMINS DATA ---
    DATA_PATH = os.path.join(PROJECT_ROOT, "data")

    ROOT_PATH = os.path.join(DATA_PATH, "raw")
    OUTPUT_PATH = os.path.join(DATA_PATH, "outputs")
    STOP_WORDS_PATH = os.path.join(DATA_PATH, "raw", "mots-vides.txt")

    # Paramètres du modèle
    WINDOW_SIZE = 25  # fenêtre de relation telle que définie
    MIN_SENTENCE_LENGTH = 5  # utilisé pour la co-occurance

    # --- FLAGS D'EXPÉRIMENTATION (Nouvelles approches) ---
    USE_CONTEXT_FILTER = True     # Filtrage contextuel verbes/adjectifs
    USE_GRAPH_DISAMBIG = True     # Désambiguïsation structurelle sur le graphe
    APPLY_GRAPH_MERGES = False    # Si True, applique les fusions suggérées par le graphe

    # --- PARAMÈTRES DU FILTRE CONTEXTUEL ---
    CONTEXT_FILTER_WINDOW = 10       # Fenêtre de tokens autour de l'entité
    CONTEXT_FILTER_THRESHOLD = -1.5  # Score sous lequel on exclut (négatif = non-humain)
    CONTEXT_FILTER_ADJ_WEIGHT = 0.7  # Poids des adjectifs vs verbes (< 1 = moins décisifs)

    # --- PARAMÈTRES DE DÉSAMBIGUÏSATION GRAPHE ---
    GRAPH_DISAMBIG_THRESHOLD = 0.4   # Seuil Jaccard pour candidats fusion
    GRAPH_DISAMBIG_MAX_MERGES = 3    # Nombre max de fusions automatiques

    # --- MÉTHODE DE POLARITÉ ---
    # "chapter_3labels" : polarité ternaire symbolique par chapitre (méthode principale)
    # "legacy"          : polarité continue à 5 classes avec pondérations (perspective)
    POLARITY_METHOD = "chapter_3labels"

    # --- COEFFICIENTS DE POLARITÉ LEGACY (Formule S_c) ---
    POLARITY_BETA = 1.2  # Poids pour les interactions de type dialogue
    POLARITY_DELTA = 2.0  # Poids pour les affiliations structurelles (famille, etc.)
    POLARITY_EPSILON = 0.05  # Poids du signal faible de cooccurrence

    # Parasites de début de phrase (Pour le nettoyage NER)
    PARASITES = ["instantanément", "soudain", "puis",
                 "galactica", "grimace de", "l’affaire", "―", "― a",
                 "cependant", "alors", "enfin", "d’"]

    BAD_TERMS = {
        # Lieux
        'trantor', 'terre', 'galaxia', 'empire', 'fondation', 'seconde fondation',
        'spacetown', 'siwenna', 'cité', 'secteur', 'mycogène', 'hélicon',
        'dahl', 'anacréon', 'streeling', 'mentone',
        # Ethnonymes
        'terrien', 'terriens', 'spaciens', 'spacien', 'médiévalistes', 'médiévaliste',
        'trantorien', 'héliconien', 'mycogénien', 'dahlite',
        # Interjections et bruits
        'voyons', 'oh', 'adieu', 'oui', 'non', 'ah', 'eh', 'hein',
        'monsieur', 'madame', 'messieurs', 'robot', 'churchill', 'jésus',
        'continuez', 'croyez-moi', 'inconnus', 'mathématicien', 'sire', 'vraiment',
        'désolé', 'pardonnez-moi', 'machinalement', 'montez', 'avisiez', 'voudriez',
        'calmez-vous', 'laissez-moi', 'mille mercis', 'respirez', 'attendez',
        'collaborez', 'reculez', 'espérez', 'guidiez', 'impossible', 'ridicule',
        'superbe', 'endormie', 'revêche', 'terraformé', 'soyez', 'chicanez',
        'bande', 'fuite', 'livre', 'assis', 'pantalon', 'idiot',
        'enc ore', 'poliment', 'voudriez-vous', 'voulez', 'hier', 'veuillez',
        'asseyez', 'regardant', 'circulât', 'blasphémant', 'digéra', 'réponds',
        'causerez', 'allez', 'auriez', 'ciel', 'shakespeare', 'heisenberg', 'adam',
        # Fragments et artefacts
        'galactica2 étouffant', 'môman ‖', 'étiez acrophobe',
        'mouleront votre crâne', 'micro-aliments', 'de-pluie quarante',
        "tite dame", "j'avisai", "l'ancien", 'kanite', 'feinta',
        'barbare seldon', 'controverse leggen', 'surprise de benastra',
        'seldon grimaça', 'seldon renifla', 'seldon sursauta',
        'seldon grommela', 'seldon sourit', 'grimace de seldon',
        'soupir de seldon', 'appelez-moi davan', 'galactica seldon',
        'jéhu galopa', 'passez-moi jessie', 'voyons jessie', 'grommela baley',
        'cher associé', 'bouche bée', 'dieu du ciel', 'affaire sarton',
        "l'affaire sarton", 'saint fastolfe', 'saint gerrigel',
        'mon cher monsieur baley',
        # Titres et fonctions seuls
        'sergent', 'descendants', 'violents', 'frère', 'sœur', 'sœurs',
        'maître', 'exo', 'primo', 'lugubre', 'emmer', 'mycélium',
        # Expressions
        'dernier empereur',

        # personnages bibliques lac3
        "jéhu", "ahab", "naboth", "jézabel", "j’avisai", "tenez", "f'", "goutte", "livraison",
        "goutte-de-pluie quarante-trois", "goutte-de-pluie quarante", "marcher",
        "le frère", "ba-lee", "bande-céleste deux",

        # ajouté dernièrement
        "p't-être", "ch'sais", "e.g", "m'dame",  # contractions mal tokenisées
        "mycogène mycogène", "a trantor", "redites",  # lieux / noms communs
        "raison", "renégat",  # noms communs capturés

        # --- FIX A : Lieux détectés comme personnages ---
        "kan", "kan kan", "aurora",

        # --- FIX D : Rôles génériques / titres / ethnonymes capturés ---
        "la fille", "la sœur", "le mycogénien",
        "fils", "fils de l'aube",
        "grand ancien", "frère honoraire",
        "bande-céleste", "bande céleste",

    }

    FALSE_POSITIVES = {
        'voir', 'avoir', 'être', 'faire', 'dire', 'pouvoir', 'devoir', 'aller',
        'vouloir', 'savoir', 'venir', 'prendre', 'donner', 'mettre',
        'petit', 'grand', 'bon', 'beau', 'jeune', 'vieux', 'nouveau',
        'premier', 'dernier', 'seul', 'même', 'autre', 'tout', 'rien'
    }

    BLACKLIST = BAD_TERMS | FALSE_POSITIVES

    T_STOP_WORDS = []

    if os.path.exists(STOP_WORDS_PATH):
        try:
            with open(STOP_WORDS_PATH, "r", encoding="utf-8") as f:
                lignes = f.readlines()
            T_STOP_WORDS = [ligne.strip() for ligne in lignes]
        except Exception as e:
            print(f"Erreur lors de la lecture des mots vides : {e}")
            T_STOP_WORDS = []
    else:
        print(f"ATTENTION : Le fichier {STOP_WORDS_PATH} est introuvable. Liste vide utilisée.")
        T_STOP_WORDS = []