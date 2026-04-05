import pytest
import spacy
from polarity_analyzer_v2 import ChapterPolarityAnalyzer
from resource_manager import ResourceManager


@pytest.mark.xfail(reason="Simple handcrafted sentence does not yet trigger polarity extraction reliably")
def test_polarity_v2_basic_relation():
    nlp = spacy.load("fr_core_news_md")

    text = "Baley aide Daneel."
    doc = nlp(text)

    res = ResourceManager.load_resources("lca")
    analyzer = ChapterPolarityAnalyzer("lca", res)

    alias_groups = [["Baley"], ["Daneel"]]
    cooc = {("Baley", "Daneel"): 1}

    result = analyzer.analyze_chapter(doc, alias_groups, cooc)

    pair = tuple(sorted(("Baley", "Daneel")))
    assert pair in result