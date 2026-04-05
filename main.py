import spacy
from flair.models import SequenceTagger
from config import Config
from preprocessor import TextPreprocessor
from ner_engine import NEREngine
from graph_builder import GraphBuilder

from resource_manager import ResourceManager
from polarity_analyzer import PolarityAnalyzer
from polarity_analyzer_v2 import ChapterPolarityAnalyzer
from context_entity_filter import ContextEntityFilter
from graph_disambiguation import GraphDisambiguator

import pandas as pd
import os
import time


def run_pipeline():
    # --- 1. INITIALISATION ---
    print("Démarrage du pipeline...")
    nlp_spacy = spacy.load("fr_core_news_md")
    tagger_flair = SequenceTagger.load("flair/ner-french")

    preprocessor = TextPreprocessor(nlp_spacy)
    ner = NEREngine(tagger_flair, nlp_spacy)
    builder = GraphBuilder()

    # --- CONFIGURATION DU MODE ---
    USE_POLARITY = True  # <--- Basculer ici
    all_submissions = []

    # Instanciation conditionnelle des nouveaux modules
    context_filter = ContextEntityFilter(nlp_spacy) if Config.USE_CONTEXT_FILTER else None
    disambiguator = GraphDisambiguator() if Config.USE_GRAPH_DISAMBIG else None

    books = {
        "lca": range(0, 18),
        "paf": range(0, 19)
        }

    for book, chapters in books.items():
        # Détermination du corpus une seule fois par livre
        corpus_type = "paf" if "paf" in book.lower() else "lca"

        # Chargement des ressources si polarité activée
        analyzer = None
        if USE_POLARITY:
            res = ResourceManager.load_resources(corpus_type)
            if Config.POLARITY_METHOD == "chapter_3labels":
                analyzer = ChapterPolarityAnalyzer(corpus_type, res)
            else:
                analyzer = PolarityAnalyzer(corpus_type, res)

        for chap in chapters:
            print(f"\n Traitement {book} - Chapitre {chap}")

            # A. Prétraitement
            raw_text = preprocessor.read_file(book, chap)
            corpus = preprocessor.clean_text(raw_text)
            corpus_filtered = preprocessor.filter_short_sentences(corpus)

            # B. Extraction NER & Résolution d'Alias
            ents_flair = ner.extract_flair(corpus_filtered, tagger=tagger_flair)
            ents_spacy = ner.extract_spacy(corpus_filtered)

            # ── NOUVEAU : Filtrage contextuel (avant le vote) ──
            all_ents = ents_flair + ents_spacy
            if context_filter:
                count_before = len([e for e in all_ents if e['type'] == 'PER'])
                all_ents = context_filter.filter_entities(
                    all_ents, corpus_filtered, verbose=True
                )
                count_after = len([e for e in all_ents if e['type'] == 'PER'])
                print(f"   -> Filtre contextuel : {count_before} PER → {count_after} PER")

            # Vote et regroupement (pipeline existant préservé)
            alias_groups = NEREngine.process_entities(
                entities=all_ents,
                book=book,
                chapter=chap
            )

            # C. Calcul des Cooccurrences (Signal de base)
            cooc = builder.compute_cooccurrences(corpus_filtered, alias_groups)

            # D. ANALYSE DE POLARITÉ (Optionnelle)
            polarity_map = None
            if USE_POLARITY and analyzer:
                doc_spacy = nlp_spacy(" ".join(corpus_filtered))
                polarity_map = analyzer.analyze_chapter(doc_spacy, alias_groups, cooc)
                print(f"   -> Polarité calculée pour {len(polarity_map)} paires.")

            # E. CRÉATION DU GRAPHE
            G, df_row = builder.create_submission_exact(
                alias_groups=alias_groups,
                cooccurrences=cooc,
                book=book,
                chapter=chap,
                polarity_map=polarity_map
            )

            # ── NOUVEAU : Désambiguïsation structurelle sur le graphe ──
            if disambiguator and G.number_of_nodes() > 2:
                report = disambiguator.generate_report(G, alias_groups, verbose=True)

                # Application optionnelle des fusions suggérées
                if Config.APPLY_GRAPH_MERGES and report['merge_candidates']:
                    alias_groups_merged = GraphDisambiguator.apply_merge_to_groups(
                        alias_groups,
                        report['merge_candidates'],
                        max_merges=Config.GRAPH_DISAMBIG_MAX_MERGES
                    )
                    # Recalcul du graphe avec les groupes fusionnés
                    cooc_new = builder.compute_cooccurrences(corpus_filtered, alias_groups_merged)
                    G, df_row = builder.create_submission_exact(
                        alias_groups=alias_groups_merged,
                        cooccurrences=cooc_new,
                        book=book,
                        chapter=chap,
                        polarity_map=polarity_map
                    )
                    print(f"   -> Graphe reconstruit après fusion ({len(alias_groups)} → {len(alias_groups_merged)} groupes)")

            all_submissions.append(df_row)

    # --- 4. EXPORT FINAL ---
    if all_submissions:
        final_df = pd.concat(all_submissions)
        os.makedirs(Config.OUTPUT_PATH, exist_ok=True)

        suffix = "_with_polarity" if USE_POLARITY else "_simple"
        if USE_POLARITY:
            suffix += f"_{Config.POLARITY_METHOD}"
        if Config.USE_CONTEXT_FILTER:
            suffix += "_ctx"
        if Config.USE_GRAPH_DISAMBIG:
            suffix += "_gd"
        output_csv = os.path.join(Config.OUTPUT_PATH, f"submission_finale{suffix}.csv")

        final_df.to_csv(output_csv, index=False)
        print(f"\n Terminé ! Fichier généré : {output_csv}")
        return final_df
    else:
        print("\nAucune donnée générée.")
        return None

if __name__ == "__main__":
    start = time.perf_counter()
    run_pipeline()
    end = time.perf_counter()

    elapsed = end - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    print(f"{minutes} min {seconds} s")