import os
import re
import unicodedata
import datetime
from config import Config


class TextPreprocessor:
    def __init__(self, nlp_model):
        self.nlp = nlp_model  # On passe le modèle chargé pour éviter de le recharger

    @staticmethod
    def corpus_formatting(text):
        """Normaliser les espaces, les paragraphes, etc."""
        text = text.replace("\n", " ").replace("\t", " ")
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    @staticmethod
    def corpus_to_phrases(corpus, model):
        """Identification des phrases avec Spacy."""
        nlp = model
        corpus = TextPreprocessor.corpus_formatting(corpus)
        doc = nlp(corpus)
        phrases = [str(sent) for sent in doc.sents]  # Convert Span objects to strings
        return phrases

    @staticmethod
    def clean_text_pipe(txt, model):
        """Prétraitement du corpus, et segmentation en phrase."""
        return TextPreprocessor.corpus_to_phrases(txt, model)

    @staticmethod
    def fix_character(corpus, character):
        """
        La segmentation en phrase avec Spacy rencontre plusieurs problèmes avec les caractères définis ci-dessous.
        Cette fonction permet de corriger cela.
        """
        new_corpus = []
        valeurs_valides = ["...", "?", ";", "!", ","]

        if character not in valeurs_valides:
            raise ValueError(f"Valeur invalide : {character}. Les valeurs possibles sont : {valeurs_valides}")

        i = 0
        while i < len(corpus):
            line = corpus[i]

            if line.endswith(str(character)):
                # Trouver les phrases suivantes qui commencent par une minuscule
                cpt = i + 1
                while cpt < len(corpus) and corpus[cpt] and corpus[cpt][0].islower():
                    cpt += 1

                # Fusionner les phrases de i à cpt-1
                merged_phrase = " ".join(corpus[i:cpt])
                new_corpus.append(merged_phrase)
                i = cpt  # Avancer jusqu'à la position cpt
            else:
                new_corpus.append(corpus[i])
                i += 1  # Avancer d'une position

        return new_corpus

    @staticmethod
    def isRoman(line: str) -> bool:
        """
        Certaines phrases du corpus extrait ne sont que des chiffres romains.
        Cette fonction permet de les détécter.
        """
        if not line:
            return False
        line = unicodedata.normalize("NFC", line)
        line_clean = re.sub(r"[^IVXLCDM]", "", line.upper())

        if not line_clean:
            return False
        pattern = r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
        return bool(re.fullmatch(pattern, line_clean))

    @staticmethod
    def clean_corpus(corpus):
        """Suppression de certains bruits dans le corpus."""
        text = []
        for phrase in corpus:

            if TextPreprocessor.isRoman(phrase):
                continue  # est-ce uniquement un chiffre romain. Si oui, ne pas l'inclure.

            if "Fondation encyclopédique" in phrase:
                phrase = phrase.replace("Fondation encyclopédique", " ")

            if "ENCYCLOPEDIA GALACTICA" in phrase:
                phrase = phrase.replace("ENCYCLOPEDIA GALACTICA", " ")

            text.append(phrase) if phrase else None

        return text

    def read_file(self, book, chapter):
        """Lecture du fichier, et extraction du corpus."""
        file_path = f"{Config.ROOT_PATH}/{book}"
        file_name = f"chapter_{chapter+ 1}.txt.preprocessed"
        with open(f"{file_path}/{file_name}", "r", encoding="utf-8") as f:
            string = f.read()
        return string

    def clean_text(self, text):
        # Ta logique clean_text + fix_character
        processed_text = TextPreprocessor.clean_text_pipe(txt=text, model=self.nlp)

        limiters = [";", "...", "?", "!"]
        for limiter in limiters:
            processed_text = TextPreprocessor.fix_character(processed_text, character=limiter)

        return TextPreprocessor.clean_corpus(processed_text)

    @staticmethod
    def filter_short_sentences(corpus):
        """Filtre les phrases trop courtes selon la Config (Critique pour le score)."""
        return [p for p in corpus if len(p.strip()) > Config.MIN_SENTENCE_LENGTH]

    @staticmethod
    def save_corpus(items, book, chapter):

        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"chapter_{chapter + 1}_{ts}.txt"
        folder = f"{Config.OUTPUT_PATH}/{book}/chap-{chapter}"

        os.makedirs(folder, exist_ok=True)  # On crée d'abord le repertoire

        with open(f"{folder}/{filename}", "w", encoding="utf-8") as f:
            for item in items:
                f.write(item + "\n")
        print(f"Corpus saved. Access path ---> : {folder}")
