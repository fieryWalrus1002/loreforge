from pathlib import Path

import pytest

DATA_RAW = Path(__file__).parent.parent / "data" / "raw"
RUN_ID = "run_test"


@pytest.fixture
def bestiary_path() -> Path:
    return DATA_RAW / "bestiary.json"


@pytest.fixture
def roster_path() -> Path:
    return DATA_RAW / "roster.json"


@pytest.fixture
def mutated_animals_path() -> Path:
    return DATA_RAW / "mutated_animals.txt"


@pytest.fixture
def robots_path() -> Path:
    return DATA_RAW / "robots.txt"


@pytest.fixture
def tmp_txt(tmp_path):
    """Factory: write a minimal .txt stat file and return its path."""
    def _make(content: str) -> Path:
        p = tmp_path / "test.txt"
        p.write_text(content)
        return p
    return _make
