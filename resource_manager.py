import json
import os
from config import Config

class ResourceManager:
    @staticmethod
    def load_resources(corpus_type):
        """
        Charge les lexiques JSON spécifiques au corpus (paf ou lca).
        On attend des fichiers nommés 'paf_resources.json' ou 'lca_resources.json'.
        """
        file_path = f"{Config.ROOT_PATH}/{corpus_type}_resources.json"
        
        if not os.path.exists(file_path):
            print(f"Ressources pour {corpus_type} introuvables. Utilisation de dictionnaires vides.")
            return {
                "LEX_SCORE": {}, "MODALS": [], "INTENSIFIERS": [], 
                "NEGATION_TOKENS": [], "AFFILIATION_PATTERNS": []
            }

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)