from preprocessor import TextPreprocessor


def test_fix_character_merges_erroneous_segmentation_around_ellipsis():
    corpus = [
        "Il hésita...",
        "puis reprit la parole.",
        "Hari Seldon arriva."
    ]

    fixed = TextPreprocessor.fix_character(corpus, "...")
    assert fixed == [
        "Il hésita... puis reprit la parole.",
        "Hari Seldon arriva."
    ]


def test_fix_character_merges_erroneous_segmentation_around_exclamation():
    corpus = [
        "Attention!",
        "dit-il en reculant.",
        "Dors observa la scène."
    ]

    fixed = TextPreprocessor.fix_character(corpus, "!")
    assert fixed == [
        "Attention! dit-il en reculant.",
        "Dors observa la scène."
    ]


def test_isRoman_detects_roman_numerals():
    assert TextPreprocessor.isRoman("XIV")
    assert TextPreprocessor.isRoman("MCMXC")
    assert not TextPreprocessor.isRoman("Hari Seldon")
    assert not TextPreprocessor.isRoman("123")


def test_clean_corpus_removes_roman_lines():
    corpus = ["XIV", "Hari Seldon entre.", "V", "Dors répond."]
    cleaned = TextPreprocessor.clean_corpus(corpus)
    assert "XIV" not in cleaned
    assert "V" not in cleaned
    assert "Hari Seldon entre." in cleaned
    assert "Dors répond." in cleaned