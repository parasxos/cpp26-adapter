"""Unit tests for the three cpp26-ref tools."""

from __future__ import annotations

import time

import pytest

from cpp26_ref.server import compiler_status, lookup_paper, search


# ---- lookup_paper ----------------------------------------------------------


def test_lookup_paper_returns_full_markdown() -> None:
    body = lookup_paper("PFIX001")
    assert body.startswith("---")
    assert "id: PFIX001" in body
    assert "Reflection" in body
    assert "enum to string" in body  # body content


def test_lookup_paper_raises_on_unknown_paper() -> None:
    with pytest.raises(FileNotFoundError) as ei:
        lookup_paper("PNOPE999")
    assert "Unknown paper id" in str(ei.value)


def test_lookup_paper_distinguishes_unauthored_from_unknown(tmp_path, monkeypatch) -> None:
    """A paper that is in index.yaml but lacks a reference file produces a
    different error message from a paper that is unknown to the index."""
    # Build a tiny corpus where one paper is indexed but unwritten.
    monkeypatch.setenv("CPP26_CORPUS_DIR", str(tmp_path))
    (tmp_path / "references").mkdir()
    (tmp_path / "index.yaml").write_text(
        "- id: PGAP001\n  title: indexed-but-unwritten\n  tier: shallow\n  ref: references/PGAP001.md\n"
    )
    from cpp26_ref import server
    server._reset_state_for_tests()

    with pytest.raises(FileNotFoundError) as ei:
        lookup_paper("PGAP001")
    assert "not yet authored" in str(ei.value)
    assert "tier=shallow" in str(ei.value)


# ---- search ----------------------------------------------------------------


def test_search_returns_topk_with_required_keys() -> None:
    results = search("reflection", top_k=3)
    assert 1 <= len(results) <= 3
    for r in results:
        assert set(r.keys()) >= {"id", "title", "tier", "category", "score", "path"}
        assert 0 <= r["score"] <= 100


def test_search_ranks_title_match_first() -> None:
    results = search("reflection", top_k=5)
    assert results[0]["id"] == "PFIX001"


def test_search_keyword_match() -> None:
    """Words that only appear in `keywords:` (not in title) still match."""
    results = search("contract_assert", top_k=3)
    ids = [r["id"] for r in results]
    assert "PFIX002" in ids


def test_search_category_match() -> None:
    results = search("concurrency", top_k=3)
    ids = [r["id"] for r in results]
    assert "PFIX003" in ids


def test_search_empty_query_returns_empty() -> None:
    assert search("", top_k=3) == []
    assert search("   ", top_k=3) == []


def test_search_top_k_respected() -> None:
    assert len(search("c++", top_k=2)) <= 2
    assert len(search("c++", top_k=5)) <= 5


# ---- compiler_status -------------------------------------------------------


def test_compiler_status_known_paper_and_compiler() -> None:
    s = compiler_status("PFIX001", "clang-22")
    assert s["paper_id"] == "PFIX001"
    assert s["compiler"] == "clang-22"
    assert s["support"] == "partial"
    assert s["informational_only"] is True


def test_compiler_status_known_paper_no_compiler_returns_all() -> None:
    s = compiler_status("PFIX001")
    assert s["paper_id"] == "PFIX001"
    assert "by_compiler" in s
    assert set(s["by_compiler"].keys()) >= {"clang-22", "clang-p2996", "gcc-16", "msvc-19.40"}


def test_compiler_status_unknown_paper_returns_unknown() -> None:
    s = compiler_status("PNOPE999", "clang-22")
    assert s["support"] == "unknown"
    assert s["informational_only"] is True


def test_compiler_status_known_paper_unknown_compiler() -> None:
    s = compiler_status("PFIX002", "icc-2024")
    assert s["support"] == "unknown"
    assert "known:" in s["note"]


def test_compiler_status_always_marks_informational() -> None:
    # Every shape of return value must carry the informational_only flag,
    # so the reviewer agent (and skill) cannot accidentally treat it as a
    # hard gate.
    for args in [("PFIX001",), ("PFIX001", "clang-22"), ("PNOPE", "clang-22")]:
        s = compiler_status(*args)
        assert s.get("informational_only") is True


# ---- performance budgets ---------------------------------------------------


def test_lookup_paper_is_fast() -> None:
    # Warm cache
    lookup_paper("PFIX001")
    start = time.perf_counter()
    for _ in range(20):
        lookup_paper("PFIX001")
    elapsed = (time.perf_counter() - start) / 20
    assert elapsed < 0.05, f"lookup_paper averaged {elapsed*1000:.1f} ms (budget 50 ms)"


def test_search_is_fast() -> None:
    # Warm cache
    search("reflection", top_k=5)
    start = time.perf_counter()
    for _ in range(20):
        search("reflection contracts senders", top_k=5)
    elapsed = (time.perf_counter() - start) / 20
    assert elapsed < 0.1, f"search averaged {elapsed*1000:.1f} ms (budget 100 ms on fixture)"
