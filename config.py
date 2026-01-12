import os


class Config:
    # Chemins
    ROOT_PATH = "./data/row"  # repertoire vers les donnéés brute
    OUTPUT_PATH = "./data/outputs"  # ex : f"{root_path}/preprocessed/"
    STOP_WORDS_PATH = "./data/mots-vides.txt"

    # Paramètres du modèle
    WINDOW_SIZE = 25  # fenêtre de relation telle que définie
    MIN_SENTENCE_LENGTH = 5  # utilisé pour la co-occurance

    # Parasites de début de phrase (Pour le nettoyage NER)
    PARASITES = ["instantanément", "soudain", "puis", "cependant", "alors", "enfin"]

    # Listes (On sort la blacklist du code métier !)
    FALSE_POSITIVES = {
        'voir', 'avoir', 'être', 'faire', 'dire', 'pouvoir', 'devoir', 'aller',
        'vouloir', 'savoir', 'venir', 'falloir', 'prendre', 'donner', 'mettre',
        'parler', 'passer', 'rester', 'rendre', 'entendre', 'attendre',
        'comprendre', 'connaître', 'croire', 'trouver', 'demander', 'regarder',
        'essayer', 'sentir', 'devenir', 'revenir', 'tenir', 'ouvrir', 'sortir',
        'petit', 'grand', 'bon', 'beau', 'jeune', 'vieux', 'nouveau', 'premier',
        'dernier', 'seul', 'même', 'autre', 'tout', 'rien', 'quelque'
    }

    # II. Termes problématiques et lieux
    # On a retiré 'dors' de cette liste pour ne pas effacer le personnage Dors Venabili
    BAD_TERMS = {
        # 1. --- BRUIT & INTERJECTIONS ---
        'voyons', 'assis', 'oh', 'adieu', 'livre', 'ciel',
        'pantalon', 'bouche bée', 'endormie', 'voyons jessie',
        'passez-moi jessie', 'dieu du ciel', 'calmez-vous',
        'oui', 'non', 'enc ore', 'poliment', 'madame', 'messieurs',
        'ben', 'ah', 'eh', 'he', 'voudriez-vous', 'blasphémant', 'digéra',
        'regardant', 'circulât', 'asseyez', 'cher associé', 'réponds', 'causerez',
        'allez', 'monsieur', 'inconnus', 'continuez', 'croyez-moi',
        'étouffant', 'montez', 'avisiez', 'machinalement', 'désolé',
        'e.g', 'revêche', 'livraison', 'impossible', 'ridicule',
        'mille mercis', 'laissez-moi', 'l’ancien', 'bande',
        'espérez', 'guidiez', 'mentone', 'respirez', 'terraformé', 'fuite',
        'j’avisai', 'môman ‖', 'étiez acrophobe', 'pardonnez-moi', 'mathématicien',

        # --- 2. LIEUX & CONCEPTS ---
        'spacetown', 'trantor', 'terre', 'galaxia', 'empire', 'fondation',
        'seconde fondation', 'siwenna', 'cité', 'secteur', 'mycogène', 'mycogène mycogène',

        # --- 3. ETHNONYMES & GROUPES ---
        'terrien', 'terriens', 'spaciens', 'spacien', 'les spaciens',
        'médiévalistes', 'médiévaliste', 'trantorien', 'héliconien',
        'mycogénien', 'le mycogénien',

        # --- 4. EXCLUSIONS SPÉCIFIQUES (HISTOIRE/NOM COMMUN) ---
        'churchill', 'jésus', 'robot', 'redites'
    }

    BLACKLIST = FALSE_POSITIVES.union(BAD_TERMS)

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