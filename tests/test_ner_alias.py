from ner_engine import NEREngine


def test_merge_alias_groups_merges_canonical_and_surface_forms():
    groupes = [
        ["Enderby"],
        ["Julius Enderby", "Julius"]
    ]

    merged = NEREngine.merge_alias_groups(groupes)

    flat_groups = [set(g) for g in merged]
    assert any({"Enderby", "Julius Enderby"} <= g for g in flat_groups)


def test_enrich_and_merge_groups_adds_original_alias_forms():
    groupes = [["Hari Seldon"], ["Dors Venabili"]]
    alias_map = {
        "Hari": "Hari Seldon",
        "Seldon": "Hari Seldon",
        "Dors": "Dors Venabili",
        "Venabili": "Dors Venabili"
    }

    enriched = NEREngine.enrich_and_merge_groups(groupes, alias_map)

    assert any(g[0] == "Hari Seldon" and "Hari" in g and "Seldon" in g for g in enriched)
    assert any(g[0] == "Dors Venabili" and "Dors" in g for g in enriched)


def test_family_guard_prevents_wrong_merge():
    """
    Cas non-régression annoncé :
    'Hari Seldon' et 'Raych Seldon' ne doivent pas fusionner.
    """
    entities = [
        {"text": "Hari Seldon", "type": "PER"},
        {"text": "Raych Seldon", "type": "PER"},
        {"text": "Hari", "type": "PER"},
        {"text": "Raych", "type": "PER"},
    ]

    groups = NEREngine.process_entities(entities=entities, book="paf", chapter=0)

    normalized = [set(g) for g in groups]
    assert any("Hari Seldon" in g for g in normalized)
    assert any("Raych Seldon" in g for g in normalized)

    # Ils doivent être dans deux groupes distincts
    hari_group = next(g for g in normalized if "Hari Seldon" in g)
    raych_group = next(g for g in normalized if "Raych Seldon" in g)
    assert hari_group is not raych_group