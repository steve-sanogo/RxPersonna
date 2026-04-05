import pandas as pd
from flair.data import Sentence
from config import Config
import re
import json
import os

"""
ALIAS_MAP MINIMAL (18 entrées)
==============================
Conserve uniquement les entrées irremplaçables par sont_lies() :
  - Alias sans AUCUN token commun (ex: "Elijah" → "Baley")
  - Protections anti-fusion (ex: "Bentley Baley" → "Bentley")
  - Artefacts NER nécessitant un traitement spécial

Toutes les autres résolutions (ex: "Hari" → "Hari Seldon", "Dr Fastolfe" → "Fastolfe")
sont gérées automatiquement par sont_lies() via les tokens partagés
et la suppression de titres.
"""

ALIAS_MAP = {

    # ── Alias sans token commun (irremplaçables) ───────────────

    # Baley (Elijah) — prénoms sans rapport avec le nom de famille
    "Elijah":               "Baley",
    "Lije":                 "Baley",

    # Daneel — "Olivaw" ne partage aucun token avec "Daneel"
    "Olivaw":               "Daneel",

    # Dors Venabili — "Maîtresse" est un titre, supprimé → chaîne vide
    "Maîtresse":            "Dors Venabili",

    # Cléon / Empereur — deux noms totalement différents, même personnage (PAF)
    "L'Empereur":           "Cléon",
    "l\u2019Empereur":           "Cléon",
    "Empereur":             "Cléon",

    # Lieutenant Alban Wellis — "Lieutenant" seul ne partage rien avec "Alban Wellis"
    "Lieutenant":           "Alban Wellis",

    # Enderby — "Julius" ne partage rien avec "Enderby"
    "Julius":               "Enderby",

    # Leggen — "Jenarr" ne partage rien avec "Leggen"
    "Jenarr":               "Leggen",

    # Vince Barrett — "Barrett" ne partage rien avec "Vince"
    "Barrett":              "Vince",

    # Mère Rittah — "Rittah" ne partage rien avec "Mère"
    "Rittah":               "Mère",

    # ── Protections anti-fusion ────────────────────────────────

    # Seldon → Hari Seldon : empêche "Seldon" d'être fusionné avec "Raych Seldon"
    "Seldon":               "Hari Seldon",

    # Bentley est le FILS de Baley, pas un alias — bloque la fusion via "baley"
    "Bentley Baley":        "Bentley",
    "Bentley":              "Bentley",

    # Mannix IV de Kan — empêche contamination par le lieu "Kan"
    "Mannix IV de Kan":     "Mannix",

    # ── Artefacts NER (nettoyage spécial) ──────────────────────

    # Le caractère ‖ et la forme composée ne sont pas nettoyés par sont_lies()
    "madame le Maire \u2016":  "Maire",
    "madame l'impératrice de Rien": "Impératrice de Rien",
}

class NEREngine:
    def __init__(self, flair_tagger, spacy_nlp):
        self.flair = flair_tagger
        self.spacy = spacy_nlp
        self.stopwords = spacy_nlp.Defaults.stop_words

    @staticmethod
    def clean_blacklist(entities):
        # Ta fonction qui filtre selon Config.BLACKLIST
        """
         D'expérience un certains nombre d'éléments sont identifiés à tort comme étant des Personnes.
         Parce qu'il sont dans la pluspart des cas en Majuscule, cette fonction y remidie.
         """

        full_blacklist = Config.BLACKLIST

        entities_propres = []

        for ent in entities:
            # On récupère le texte, on nettoie les espaces et on met en minuscule
            nom_raw = ent.get('text', '').strip()
            nom_clean = nom_raw.lower()

            # Si le mot est dans la blacklist, on le saute
            if nom_clean in full_blacklist:
                continue

            # Sécurité pour les mots très courts (souvent du bruit comme "M.", "L'")
            # On garde 'R.' (pour R. Daneel) mais on supprime les autres trucs de 1 lettre
            if len(nom_clean) < 2 and nom_clean != "r.":
                continue

            # Si tout est bon, on garde l'entité
            entities_propres.append(ent)

        return entities_propres

    @staticmethod
    def convert_spacy_label(spacy_label):
        """Convertit les labels spaCy vers celui de FLAIR"""
        label_mapping = {
            'PER': 'PER',  # Personne
            'PERSON': 'PER',  # Alternative selon le modèle
            'LOC': 'LOC',  # Lieu
            'GPE': 'LOC',  # Géopolitique → Lieu
            'ORG': 'ORG',  # Organisation
            'MISC': 'ORG'  # Divers → Organisation
        }
        return label_mapping.get(spacy_label, spacy_label)

    def extract_flair(self, corpus, tagger):
        # Ta fonction NER_with_flair nettoyée (avec le regex et Config.PARASITES)
        """Extraction des EN avec FLAIR."""

        flair_entities = []
        # Assurez-vous d'avoir chargé le modèle tagger hors de la boucle ou ici

        parasites_debut = Config.PARASITES

        for phrase in corpus:
            if len(phrase.strip()) < 2: continue

            sentence = Sentence(phrase)
            tagger.predict(sentence, verbose=False)

            for ent in sentence.get_spans('ner'):
                if ent.get_label('ner').value in ["PER", "LOC", "ORG"]:

                    # 1. Nettoyage initial
                    texte_propre = ent.text.strip()

                    # 2. Supprimer chiffres/puces au début ("2 Elijah")
                    texte_propre = re.sub(r'^[\d\-\.\)]+\s*', '', texte_propre)

                    # 3. Nettoyage agressif ponctuation ("Ben !")
                    # texte_propre = texte_propre.strip(" ,!?;:\"'«»()[]*—–-")

                    texte_propre = texte_propre.strip(" ,!?;:\"'«»()[]*—–-‖―") # ajout
                    texte_propre = re.sub(r"^[dl][''\u2019]\s*", "", texte_propre, flags=re.IGNORECASE) # ajout

                    # 4. Supprimer les parasites de début ("Instantanément...")
                    lower_text = texte_propre.lower()
                    for parasite in parasites_debut:
                        if lower_text.startswith(parasite + " "):
                            texte_propre = texte_propre[len(parasite):].strip(" ,!?;:\"'«»")
                            break

                    # 5. Gestion du point final (R. vs Fin de phrase)
                    lower_text = texte_propre.lower()
                    if texte_propre.endswith('.'):
                        if len(texte_propre) > 2 and lower_text not in ["mr.", "dr.", "pr.", "st."]:
                            texte_propre = texte_propre.rstrip('.')
                            lower_text = texte_propre.lower()

                    # 6. Filtre final
                    if (lower_text not in self.stopwords and lower_text not in Config.T_STOP_WORDS):
                        flair_entities.append({
                            'text': texte_propre,  # On garde la version propre (avec Majuscules)
                            'type': ent.get_label('ner').value
                        })

        # Appel de la blacklist
        return NEREngine.clean_blacklist(flair_entities)

    def extract_spacy(self, corpus, batch_size=50):
        # Ta fonction NER_with_spacy_batch nettoyée
        spacy_entities = []
        parasites_debut = Config.PARASITES

        valid_phrases = [phrase for phrase in corpus if len(phrase.strip()) > 0]

        for i in range(0, len(valid_phrases), batch_size):
            batch = valid_phrases[i:i + batch_size]
            docs = list(self.spacy.pipe(batch))

            for doc in docs:
                for ent in doc.ents:
                    entity_type = NEREngine.convert_spacy_label(ent.label_)

                    if entity_type in ["PER", "LOC", "ORG"]:
                        # --- MEME LOGIQUE DE NETTOYAGE QUE FLAIR ---
                        texte_propre = ent.text.strip()
                        texte_propre = re.sub(r'^[\d\-\.\)]+\s*', '', texte_propre)
                        texte_propre = texte_propre.strip(" ,!?;:\"'«»()[]*—–-")

                        lower_text = texte_propre.lower()
                        for parasite in parasites_debut:
                            if lower_text.startswith(parasite + " "):
                                texte_propre = texte_propre[len(parasite):].strip(" ,!?;:\"'«»")
                                break

                        lower_text = texte_propre.lower()
                        if texte_propre.endswith('.'):
                            if len(texte_propre) > 2 and lower_text not in ["mr.", "dr.", "pr.", "st."]:
                                texte_propre = texte_propre.rstrip('.')
                                lower_text = texte_propre.lower()

                        if (lower_text not in self.stopwords and lower_text not in Config.T_STOP_WORDS):
                            spacy_entities.append({
                                'text': texte_propre,
                                'type': entity_type
                            })

        return NEREngine.clean_blacklist(spacy_entities)

    @staticmethod
    def process_ner_comparison(flair_entities, spacy_entities):
        """Compare Flair et spaCy sur le même corpus"""

        # Statistiques comparatives
        print(f"\n--- COMPARAISON ---")
        print(f"Flair: {len(flair_entities)} entités")
        print(f"spaCy: {len(spacy_entities)} entités")

        # Types d'entités trouvés
        flair_types = pd.DataFrame(flair_entities)['type'].value_counts()
        spacy_types = pd.DataFrame(spacy_entities)['type'].value_counts()

        print(f"\nFlair - Types: {dict(flair_types)}")
        print(f"spaCy - Types: {dict(spacy_types)}")

        # Affichage des différences
        print(f"\n--- Différences Entités personnes---")

        flair_pern = [entity for entity in flair_entities if entity['type'] == 'PER']
        spacy_pern = [entity for entity in spacy_entities if entity['type'] == 'PER']

        if len(flair_pern) >= len(spacy_pern):
            print("EN en plus dans Flair :")
            for entity in flair_pern:
                if entity not in spacy_pern:
                    print(entity, sep='\t')
        else:
            print("EN en plus dans spaCy :")
            for entity in spacy_pern:
                if entity not in flair_pern:
                    print(entity, sep='\t')
        pass

    @staticmethod
    def get_genre(nom):
        titres_masculins = {'Mr', 'Monsieur', 'M.', 'Sir', 'Mr.', 'M'}
        titres_feminins = {'Mme', 'Madame', 'Mademoiselle', 'Miss', 'Ms', 'Mme.', 'Mlle'}
        mots = set(nom.split())
        if any(mot in titres_masculins or mot.lower() in {t.lower() for t in titres_masculins} for mot in mots):
            return 'masculin'
        if any(mot in titres_feminins or mot.lower() in {t.lower() for t in titres_feminins} for mot in mots):
            return 'feminin'
        return None  # neutre si pas de titre

    @staticmethod
    def genre_compatible(genre_groupe, genre_personne):
        if genre_groupe == 'feminin':
            return genre_personne == 'feminin'
        elif genre_groupe == 'masculin':
            return genre_personne == 'masculin' or genre_personne is None
        elif genre_groupe is None:
            return genre_personne == 'masculin' or genre_personne is None
        return False

    @staticmethod
    def supprimer_titres(nom):
        titres = [
            # Titres déjà présents
            'mr', 'mme', 'monsieur', 'madame', 'm.', 'dr', 'sir', 'miss', 'ms', 'mademoiselle',
            'mr.', 'mme.', 'mlle', 'Mr', 'Mme', 'Monsieur', 'Madame', 'M.', 'Dr', 'Sir', 'Miss',
            'Ms', 'Mademoiselle', 'Mr.', 'Mme.', 'Mlle', "R.",
            # AJOUT : titres français manquants (cause du Bug n°1)
            'docteur', 'Docteur',
            'maître', 'Maître',
            'maîtresse', 'Maîtresse',
            'professeur', 'Professeur',
        ]
        mots = nom.split()
        mots_sans_titres = [mot for mot in mots if mot.lower() not in [t.lower() for t in titres]]
        return ' '.join(mots_sans_titres)

    @staticmethod
    def sont_lies(nom1, nom2):
        n1 = NEREngine.supprimer_titres(nom1).lower().strip()
        n2 = NEREngine.supprimer_titres(nom2).lower().strip()

        # AJOUT : garde si un nom devient vide après suppression des titres
        # (ex: "Maître" seul → "" après suppression)
        if not n1 or not n2:
            return False

        if n1 == n2:
            return True

        # --- FIX C : Protection ALIAS_MAP ---
        # Si les deux noms pointent vers des canoniques différents,
        # on interdit la fusion (ex: "Bentley Baley" → Bentley ≠ "Baley" → Baley)
        # Un nom peut être une CLÉ dans ALIAS_MAP (ex: "Elijah" → "Baley")
        # OU un CANONIQUE, c.à.d. une VALEUR (ex: "Baley" est lui-même canonique)
        canon1 = ALIAS_MAP.get(nom1, ALIAS_MAP.get(nom1.title(), None))
        canon2 = ALIAS_MAP.get(nom2, ALIAS_MAP.get(nom2.title(), None))

        # Si un nom n'est pas une clé mais EST un canonique (valeur), il se représente lui-même
        _all_canonicals = set(ALIAS_MAP.values())
        if canon1 is None and nom1 in _all_canonicals:
            canon1 = nom1
        if canon2 is None and nom2 in _all_canonicals:
            canon2 = nom2

        if canon1 and canon2 and canon1 != canon2:
            return False

        mots1 = set(n1.split())
        mots2 = set(n2.split())
        commun = mots1 & mots2

        if not commun:
            return False

        # --- SECURITE FAMILLE ---
        if len(mots1) > 1 and len(mots2) > 1:
            prenom1 = n1.split()[0]
            prenom2 = n2.split()[0]

            compatible_initiale = (
                    (len(prenom1) == 2 and prenom1[1] == '.' and prenom2.startswith(prenom1[0])) or
                    (len(prenom2) == 2 and prenom2[1] == '.' and prenom1.startswith(prenom2[0]))
            )

            if prenom1 != prenom2 and not compatible_initiale:
                return False

        return True

    @staticmethod
    def save_alias(rslt, path):
        with open(f"{path}/alias.txt", "w", encoding="utf-8") as f:
            for groupe in rslt:
                ligne = "{" + ", ".join(groupe) + "}"
                f.write(ligne + "\n")
        return True

    @staticmethod
    def resolve_aliases(noms, save_path):
        groupes = []
        noms_tries = sorted(noms, key=lambda x: len(x.split()), reverse=True)
        liens = {nom: set() for nom in noms_tries}

        for nom1 in noms_tries:
            for nom2 in noms_tries:
                if nom1 != nom2 and NEREngine.sont_lies(nom1, nom2):
                    liens[nom1].add(nom2)

        vus = set()
        for nom in noms_tries:
            if nom in vus:
                continue

            groupe = set()
            pile = [nom]
            genre_groupe = NEREngine.get_genre(nom)
            # AJOUT : représentant canonique du groupe (nom le plus long, traité en premier)
            representant = nom

            while pile:
                courant = pile.pop()
                if courant in vus or courant in groupe:
                    continue

                genre_personne = NEREngine.get_genre(courant)
                if not NEREngine.genre_compatible(genre_groupe, genre_personne):
                    continue

                # AJOUT : vérification contre le représentant canonique
                # Empêche les fusions transitives via un alias ambigu (ex: "Seldon"
                # qui lierait "Hari Seldon" et "Raych Seldon" en passant par lui)
                if courant != representant and not NEREngine.sont_lies(representant, courant):
                    continue

                vus.add(courant)
                groupe.add(courant)
                pile.extend(liens[courant] - vus)

            groupe_sans_titres = [n for n in groupe if NEREngine.supprimer_titres(n) == n]
            groupe_avec_titres = [n for n in groupe if NEREngine.supprimer_titres(n) != n]
            groupe_trie = sorted(groupe_sans_titres) + sorted(groupe_avec_titres)
            groupes.append(groupe_trie)

        NEREngine.save_alias(rslt=groupes, path=save_path)
        return groupes

    @staticmethod
    def merge_alias_groups(groupes):
        """
        Fusionne les groupes dont le canonique est déjà présent dans le chapitre.
        Résout les conflits intra-chapitres (ex: 'Hari' et 'Hari Seldon' dans le même chapitre).
        """
        # 1. Construire un index : canonical -> index du groupe dans la liste
        canonical_to_idx = {}
        for idx, groupe in enumerate(groupes):
            for nom in groupe:
                canonical = ALIAS_MAP.get(nom, nom)
                # On cherche si ce canonical est lui-même chef d'un groupe existant
                for idx2, groupe2 in enumerate(groupes):
                    if canonical in groupe2:
                        canonical_to_idx[canonical] = idx2
                        break

        # 2. Pour chaque groupe, vérifier si un de ses membres pointe vers un autre groupe
        merged = [True] * len(groupes)  # True = groupe encore actif
        groupes_result = [list(g) for g in groupes]

        for idx, groupe in enumerate(groupes):
            if not merged[idx]:
                continue
            for nom in groupe:
                canonical = ALIAS_MAP.get(nom, nom)
                if canonical != nom and canonical in canonical_to_idx:
                    target_idx = canonical_to_idx[canonical]
                    if target_idx != idx and merged[target_idx]:
                        # Fusion : on verse le groupe courant dans le groupe cible
                        groupes_result[target_idx].extend(
                            [n for n in groupes_result[idx] if n not in groupes_result[target_idx]]
                        )
                        merged[idx] = False  # Ce groupe est absorbé
                        break

        return [g for i, g in enumerate(groupes_result) if merged[i]]


    @staticmethod
    def enrich_and_merge_groups(groupes, alias_map):
        """
        1. Ajoute les formes originales de l'ALIAS_MAP dans chaque groupe
           (pour que compute_cooccurrences les retrouve dans le texte)
        2. Fusionne les groupes qui partagent le même canonical
        """
        # Reverse map : canonical -> [formes originales]
        from collections import defaultdict
        canon_to_originals = defaultdict(set)
        for original, canonical in alias_map.items():
            canon_to_originals[canonical].add(original)

        # Pour chaque groupe, identifier son canonical et récupérer toutes ses formes
        def get_canonical(groupe):
            for nom in groupe:
                if nom in alias_map:
                    return alias_map[nom]
            return groupe[0]  # déjà canonique

        # Regrouper par canonical
        merged = defaultdict(set)
        for groupe in groupes:
            canonical = get_canonical(groupe)
            merged[canonical].update(groupe)
            # Ajouter toutes les formes originales connues pour ce canonical
            merged[canonical].update(canon_to_originals.get(canonical, set()))

        # Reconstruire les listes : canonical en premier, puis le reste
        result = []
        for canonical, members in merged.items():
            members.discard(canonical)
            groupe_final = [canonical] + sorted(members)
            result.append(groupe_final)

        return result

    @staticmethod
    def process_entities(entities, book, chapter):
        entities = [
            {**e, 'text': e['text'].replace('\u2019', "'").replace('\u2018', "'")}
            for e in entities
        ]
        # On s'assure que pandas est bien importé (sinon ajoute import pandas as pd en haut du fichier)
        df = pd.DataFrame.from_records(entities)

        # 1. Compter les occurrences par type
        sorted_df = df.groupby(['text', 'type']).size().reset_index(name='counts')

        # GESTION DES ÉGALITÉS ---
        # PER = 1 (prioritaire), les autres = 2.
        sorted_df['priority'] = sorted_df['type'].apply(lambda x: 1 if x == 'PER' else 2)

        # On trie : Text -> Vote majoritaire -> Priorité PER
        sorted_df = sorted_df.sort_values(by=['text', 'counts', 'priority'], ascending=[True, False, True])

        # On ne garde que le vainqueur
        sorted_df_max = sorted_df.drop_duplicates(subset=['text'], keep='first').copy()

        # Nettoyage
        sorted_df_max = sorted_df_max.drop(columns=['priority'])

        doc_path = f"{Config.OUTPUT_PATH}/{book}/chap-{chapter}"

        # Boucle d'export des fichiers
        types = ["PER", "LOC", "ORG"]
        for ent_type in types:
            df_type = sorted_df_max[sorted_df_max["type"] == ent_type]
            df_export = df_type[["text"]]

            output_file = f"{doc_path}/resultat_{ent_type}.txt"
            os.makedirs(doc_path, exist_ok=True)  # On s'assure que le dossier existe (sécurité)

            df_export.to_csv(output_file, sep="\t", index=False, header=False)
            print(f"{ent_type} exporté dans : {output_file}")

        # Export des métadonnées
        result_list = []
        for text, group in sorted_df.groupby("text"):
            type_list = [{row["type"]: row["counts"]} for _, row in group.iterrows()]
            result_list.append({text: type_list})

        with open(doc_path + "/NER_metadata.json", "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

        clr_id = sorted_df_max.shape[0]
        print(f"{clr_id} EN identifiées (avec priorité PER en cas d'égalité).")

        # On filtre le dataframe final pour ne garder que les PER
        # et on retourne une liste Python simple (ex: ['Hari Seldon', 'Dors', ...])
        per_entities_list = sorted_df_max[sorted_df_max["type"] == "PER"]["text"].tolist()

        groupes = NEREngine.resolve_aliases(noms=per_entities_list, save_path=doc_path)
        groupes = NEREngine.enrich_and_merge_groups(groupes, ALIAS_MAP)
        return groupes