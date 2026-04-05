from resource_manager import ResourceManager
from extraction_rules import ExtractionRules


def test_resource_manager_loads_lca_resources():
    res = ResourceManager.load_resources("lca")
    assert isinstance(res, dict)
    assert "LEX_AMI" in res
    assert "LEX_ENNEMI" in res


def test_resource_manager_loads_paf_resources():
    res = ResourceManager.load_resources("paf")
    assert isinstance(res, dict)
    assert "LEX_AMI" in res
    assert "LEX_ENNEMI" in res


def test_extraction_rules_3labels():
    assert ExtractionRules.get_label_3(1.0) == "ami"
    assert ExtractionRules.get_label_3(-1.0) == "ennemi"
    assert ExtractionRules.get_label_3(0.0) == "neutre"