import os


class Config:
    # Chemins
    ROOT_PATH = "./data/row"  # repertoire vers les donnéés brute
    OUTPUT_PATH = "./data/outputs"  # ex : f"{root_path}/preprocessed/"
    STOP_WORDS_PATH = "./data/mots-vides.txt"

    # Paramètres du modèle
    WINDOW_SIZE = 25  # fenêtre de relation telle que définie
    MIN_SENTENCE_LENGTH = 5  # utilisé pour la co-occurance

    # --- COEFFICIENTS DE POLARITÉ (Formule S_c) ---
    POLARITY_BETA = 1.2  # Poids pour les interactions de type dialogue
    POLARITY_DELTA = 2.0  # Poids pour les affiliations structurelles (famille, etc.)
    POLARITY_EPSILON = 0.05  # Poids du signal faible de cooccurrence

    # Parasites de début de phrase (Pour le nettoyage NER)
    PARASITES = ["instantanément", "soudain", "puis", "cependant", "alors", "enfin"]

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
        'dernier empereur', "l'empereur",
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