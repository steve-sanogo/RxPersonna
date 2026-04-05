import xml.etree.ElementTree as ET

from graph_builder import GraphBuilder
from config import Config


def test_compute_cooccurrences_creates_edge_within_window(sample_corpus_phrases, sample_alias_groups):
    builder = GraphBuilder()
    cooc = builder.compute_cooccurrences(
        sample_corpus_phrases,
        sample_alias_groups,
        window_size=25
    )

    assert ("Baley", "Enderby") in cooc or ("Enderby", "Baley") in cooc
    assert any("Baley" in pair and "Daneel" in pair for pair in cooc)


def test_compute_cooccurrences_respects_small_window():
    builder = GraphBuilder()

    corpus = ["Hari Seldon " + "mot " * 40 + "Dors Venabili"]
    alias_groups = [["Hari Seldon"], ["Dors Venabili"]]

    cooc_small = builder.compute_cooccurrences(corpus, alias_groups, window_size=5)
    cooc_large = builder.compute_cooccurrences(corpus, alias_groups, window_size=50)

    assert len(cooc_small) == 0
    assert len(cooc_large) == 1


def test_create_submission_exact_includes_polarity_attributes(temp_output_dir):
    builder = GraphBuilder()
    alias_groups = [["Baley", "Elijah Baley"], ["Daneel", "R. Daneel"]]
    cooccurrences = {("Baley", "Daneel"): 3}
    polarity_map = {("Baley", "Daneel"): 1.0}

    old_method = Config.POLARITY_METHOD
    Config.POLARITY_METHOD = "chapter_3labels"
    try:
        graph, df = builder.create_submission_exact(
            alias_groups=alias_groups,
            cooccurrences=cooccurrences,
            book="lca",
            chapter=0,
            polarity_map=polarity_map
        )
    finally:
        Config.POLARITY_METHOD = old_method

    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1

    edge_data = graph.get_edge_data("Baley", "Daneel")
    assert edge_data["weight"] == 3
    assert edge_data["polarity_score"] == 1.0
    assert edge_data["polarity_label"] == "ami"

    assert list(df.columns) == ["ID", "graphml"]
    assert df.iloc[0]["ID"] == "lca0"


def test_create_submission_exact_prunes_isolated_nodes(temp_output_dir):
    builder = GraphBuilder()
    alias_groups = [["Baley"], ["Daneel"], ["Enderby"]]
    cooccurrences = {("Baley", "Daneel"): 2}

    graph, _ = builder.create_submission_exact(
        alias_groups=alias_groups,
        cooccurrences=cooccurrences,
        book="lca",
        chapter=1,
        polarity_map=None
    )

    assert "Enderby" not in graph.nodes


def test_exported_graphml_is_valid_xml(temp_output_dir):
    builder = GraphBuilder()
    alias_groups = [["Baley"], ["Daneel"]]
    cooccurrences = {("Baley", "Daneel"): 1}

    _, df = builder.create_submission_exact(
        alias_groups=alias_groups,
        cooccurrences=cooccurrences,
        book="lca",
        chapter=2
    )

    graphml_str = df.iloc[0]["graphml"]
    root = ET.fromstring(graphml_str)
    assert root.tag.endswith("graphml")