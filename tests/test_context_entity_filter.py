import spacy

from context_entity_filter import ContextEntityFilter


def test_filter_runs_on_simple_input():
    nlp = spacy.load("fr_core_news_md")
    filt = ContextEntityFilter(nlp)

    entities = [
        {"text": "Trantor", "type": "PER"},
        {"text": "Hari Seldon", "type": "PER"}
    ]

    corpus_filtered = [
        "Hari Seldon parle calmement avec Dors.",
        "Trantor est une planète très vaste."
    ]

    filtered = filt.filter_entities(entities, corpus_filtered)

    assert filtered is not None
    assert isinstance(filtered, list)