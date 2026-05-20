"""Test fixtures for cpp26-ref MCP server tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_CORPUS = TESTS_DIR / "fixtures" / "corpus"

# Make src/ importable without `pip install -e .` when running pytest directly.
sys.path.insert(0, str(TESTS_DIR.parent / "src"))


@pytest.fixture(autouse=True)
def use_fixture_corpus(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point CorpusState at the fixture corpus and reset the in-memory cache."""
    monkeypatch.setenv("CPP26_CORPUS_DIR", str(FIXTURE_CORPUS))
    from cpp26_ref import server
    server._reset_state_for_tests()
