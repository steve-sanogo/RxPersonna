import spacy

from preprocessor import TextPreprocessor
from graph_builder import GraphBuilder


def test_preprocessing_to_cooccurrence_chain():
    nlp = spacy.load("fr_core_news_md")
    preprocessor = TextPreprocessor(nlp)
    builder = GraphBuilder()

    raw_text = "Hari Seldon parle à Dors Venabili. Dors répond calmement."
    corpus = preprocessor.clean_text(raw_text)
    corpus_filtered = preprocessor.filter_short_sentences(corpus)

    alias_groups = [["Hari Seldon", "Hari"], ["Dors Venabili", "Dors"]]
    cooc = builder.compute_cooccurrences(corpus_filtered, alias_groups, window_size=25)

    assert len(corpus_filtered) > 0
    assert any("Hari Seldon" in pair and "Dors Venabili" in pair for pair in cooc)