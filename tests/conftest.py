import shutil
import tempfile
import pytest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from  config import Config

@pytest.fixture
def temp_output_dir(monkeypatch):
    """
    Redirige Config.OUTPUT_PATH vers un dossier temporaire
    pour éviter d'écrire dans les vraies sorties du projet.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ams_tests_")
    monkeypatch.setattr(Config, "OUTPUT_PATH", tmp_dir)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def sample_alias_groups():
    return [
        ["Enderby", "Julius Enderby"],
        ["Baley", "Elijah Baley", "Elijah", "Lije"],
        ["Daneel", "R. Daneel", "Daneel Olivaw"]
    ]


@pytest.fixture
def sample_corpus_phrases():
    return [
        "Enderby parle à Baley dans le bureau.",
        "Baley répond à Daneel calmement.",
        "Plus tard Enderby revoit Baley."
    ]