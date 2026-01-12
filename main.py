import spacy
from flair.models import SequenceTagger
from config import Config
from preprocessor import TextPreprocessor
from ner_engine import NEREngine
from graph_builder import GraphBuilder
import pandas as pd
import os


def main():
    # 1. Chargement unique des modèles (Gain de temps énorme)
    print("Chargement des modèles...")
    nlp_spacy = spacy.load("fr_core_news_md")

    # On charge le tagger ici et on le passera au moteur
    tagger_flair = SequenceTagger.load("flair/ner-french")

    # 2. Instanciation des classes
    preprocessor = TextPreprocessor(nlp_spacy)
    ner = NEREngine(tagger_flair, nlp_spacy)
    builder = GraphBuilder()

    all_submissions = []

    # 3. Boucle sur les livres
    # Assure-toi que la clé "paf" correspond bien au nom du dossier dans ./data/paf
    books = {"lca": range(0, 18),
             "paf": range(0, 19)
             }

    for book, chapters in books.items():
        for chap in chapters:
            print(f"\n Traitement {book} - Chapitre {chap}")

            # A. Lecture & Nettoyage
            raw_text = preprocessor.read_file(book, chap)
            corpus = preprocessor.clean_text(raw_text)

            # Sauvegarde du corpus brut nettoyé (pour débug si besoin)
            TextPreprocessor.save_corpus(items=corpus, book=book, chapter=chap)

            # --- LE FILTRE CRUCIAL (Garde-le !) ---
            # On ne garde que les phrases > 5 chars pour le NER
            corpus_filtered = preprocessor.filter_short_sentences(corpus)
            print(f"   -> Phrases retenues pour NER : {len(corpus_filtered)} / {len(corpus)}")

            # B. Extraction NER 'propres'
            # Note: ner.extract_flair utilise self.flair ou l'argument tagger selon ta classe.
            # Comme tu as passé tagger_flair dans le __init__ de NEREngine,
            # vérifie si extract_flair a besoin de l'argument 'tagger' ou utilise 'self.flair'.
            # Dans le doute, ta syntaxe actuelle fonctionne.
            ents_flair = ner.extract_flair(corpus_filtered, tagger=tagger_flair)
            ents_spacy = ner.extract_spacy(corpus_filtered)

            # C. Comparaison (Juste pour info dans la console)
            NEREngine.process_ner_comparison(flair_entities=ents_flair, spacy_entities=ents_spacy)

            # D. Résolution complète (Vote + Regroupement Alias)
            # Cette fonction retourne maintenant les GROUPES d'alias (ex: [['Hari', 'Seldon'], ['Dors']])
            alias_groups = NEREngine.process_entities(entities=ents_flair + ents_spacy, book=book, chapter=chap)

            # E. Création du Graphe & Soumission
            cooc = builder.compute_cooccurrences(corpus_filtered, alias_groups)

            # Note: create_submission_exact sauvegarde déjà le fichier individuel
            _, df_row = builder.create_submission_exact(alias_groups=alias_groups, cooccurrences=cooc, book=book,
                                                        chapter=chap)

            all_submissions.append(df_row)

    # 4. Fusion finale pour le leaderboard
    if all_submissions:
        final_df = pd.concat(all_submissions)
        # On s'assure que le dossier de sortie existe
        os.makedirs(Config.OUTPUT_PATH, exist_ok=True)

        output_csv = os.path.join(Config.OUTPUT_PATH, "submission_finale.csv")
        final_df.to_csv(output_csv, index=False)
        print(f"\nTerminé ! Fichier final généré : {output_csv}")
    else:
        print("\nAucune donnée générée.")


if __name__ == "__main__":
    main()