from graph_builder import GraphBuilder
from resource_manager import ResourceManager
from ner_engine import NEREngine


def test_non_regression_family_seldon():
    entities = [
        {"text": "Hari Seldon", "type": "PER"},
        {"text": "Raych Seldon", "type": "PER"},
        {"text": "Hari", "type": "PER"},
        {"text": "Raych", "type": "PER"},
    ]
    groups = NEREngine.process_entities(entities=entities, book="paf", chapter=99)
    normalized = [set(g) for g in groups]

    hari_group = next(g for g in normalized if "Hari Seldon" in g)
    raych_group = next(g for g in normalized if "Raych Seldon" in g)

    assert hari_group != raych_group


def test_non_regression_cooccurrence_reference_case():
    builder = GraphBuilder()
    corpus = [
        "Hari Seldon rencontre Dors Venabili.",
        "Plus tard Hari reparle à Dors."
    ]
    alias_groups = [["Hari Seldon", "Hari"], ["Dors Venabili", "Dors"]]

    cooc = builder.compute_cooccurrences(corpus, alias_groups, window_size=25)
    pair = tuple(sorted(("Hari Seldon", "Dors Venabili")))
    assert cooc[pair] >= 1


def test_non_regression_resources_still_load():
    for corpus in ["lca", "paf"]:
        res = ResourceManager.load_resources(corpus)
        assert "LEX_AMI" in res
        assert "LEX_ENNEMI" in res