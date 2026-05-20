"""cpp26-ref MCP server — three stdio tools backing the cpp26-adapter plugin.

Tools:
  * lookup_paper(paper_id)            — return the markdown reference for a paper
  * search(query, top_k=5)            — fuzzy + keyword match over the index
  * compiler_status(paper_id, [comp]) — read the compiler-status matrix

Corpus location is resolved as (in priority order):
  1. CPP26_CORPUS_DIR environment variable
  2. <repo>/corpus, computed as four parents up from this file

The server loads index.yaml and status.yaml once at startup. If either is
missing the server still runs — search returns an empty list, compiler_status
returns "unknown" — so the MCP can be installed before the corpus is fully
populated.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP
from rapidfuzz import fuzz, process

DEFAULT_CORPUS = Path(__file__).resolve().parents[3] / "corpus"


def _corpus_dir() -> Path:
    return Path(os.environ.get("CPP26_CORPUS_DIR", str(DEFAULT_CORPUS)))


class CorpusState:
    """In-memory snapshot of the C++26 corpus.

    Loaded once when the first tool call lands, then reused. Reload requires
    restarting the server (the corpus only changes between sessions during
    quarterly refreshes).
    """

    def __init__(self, corpus_dir: Path) -> None:
        self.corpus_dir = corpus_dir
        self.references_dir = corpus_dir / "references"
        self.index: list[dict[str, Any]] = []
        self.status: dict[str, dict[str, Any]] = {}
        self._reload()

    def _reload(self) -> None:
        index_path = self.corpus_dir / "index.yaml"
        if index_path.exists():
            data = yaml.safe_load(index_path.read_text()) or []
            self.index = data if isinstance(data, list) else []
        status_path = self.corpus_dir / "status.yaml"
        if status_path.exists():
            data = yaml.safe_load(status_path.read_text()) or {}
            self.status = data if isinstance(data, dict) else {}

    def lookup_paper(self, paper_id: str) -> str:
        ref_path = self.references_dir / f"{paper_id}.md"
        if not ref_path.exists():
            row = next((r for r in self.index if r.get("id") == paper_id), None)
            if row is None:
                raise FileNotFoundError(
                    f"Unknown paper id {paper_id!r}. Not in corpus/index.yaml."
                )
            raise FileNotFoundError(
                f"Reference not yet authored for {paper_id} "
                f"(tier={row.get('tier')}, expected at {ref_path})."
            )
        return ref_path.read_text()

    def search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if not self.index or not query.strip():
            return []
        # Build searchable text per row: title doubled (×2 weight), keywords, category.
        choices: list[str] = []
        for row in self.index:
            title = str(row.get("title", ""))
            kws_field = row.get("keywords", []) or []
            kws = " ".join(str(k) for k in kws_field)
            cat = str(row.get("category", ""))
            choices.append(f"{title} {title} {kws} {cat}".strip())
        matches = process.extract(query, choices, scorer=fuzz.WRatio, limit=top_k)
        return [
            {
                "id": self.index[idx]["id"],
                "title": self.index[idx].get("title", ""),
                "tier": self.index[idx].get("tier", "stub"),
                "category": self.index[idx].get("category", "other"),
                "score": int(round(score)),
                "path": self.index[idx].get("ref", ""),
            }
            for _, score, idx in matches
        ]

    def compiler_status(self, paper_id: str, compiler: str | None) -> dict[str, Any]:
        entry = self.status.get(paper_id)
        if entry is None:
            return {
                "paper_id": paper_id,
                "compiler": compiler,
                "support": "unknown",
                "note": "no status data; paper not present in corpus/status.yaml",
                "informational_only": True,
            }
        if compiler is None:
            return {
                "paper_id": paper_id,
                "by_compiler": entry,
                "informational_only": True,
            }
        compiler_entry = entry.get(compiler)
        if compiler_entry is None:
            return {
                "paper_id": paper_id,
                "compiler": compiler,
                "support": "unknown",
                "note": f"no entry for {compiler!r}; known: {sorted(entry.keys())}",
                "informational_only": True,
            }
        return {
            "paper_id": paper_id,
            "compiler": compiler,
            **compiler_entry,
            "informational_only": True,
        }


_state: CorpusState | None = None


def _get_state() -> CorpusState:
    global _state
    if _state is None:
        _state = CorpusState(_corpus_dir())
    return _state


def _reset_state_for_tests() -> None:
    """Test helper — re-read corpus from disk on next tool call."""
    global _state
    _state = None


mcp = FastMCP("cpp26-ref")


@mcp.tool()
def lookup_paper(paper_id: str) -> str:
    """Return the full markdown reference for a C++26 paper.

    Args:
        paper_id: WG21 paper identifier (e.g. 'P2996', 'P2900').

    Returns:
        The contents of corpus/references/<paper_id>.md, including the YAML
        frontmatter (id, title, revision, tier, keywords, canonical_url, …)
        and the prose body (problem, syntax, canonical example, pre-C++26
        equivalent, gotchas, related).

    Raises:
        FileNotFoundError when the paper is unknown to the index, or known
        but its reference markdown has not yet been authored.
    """
    return _get_state().lookup_paper(paper_id)


@mcp.tool()
def search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Free-text search over the C++26 paper index.

    Matches against title (weighted ×2), keywords, and category using
    rapidfuzz's WRatio scorer (a robust fuzzy match for short strings).

    Args:
        query: free-text query, e.g. 'reflection', 'enum to string',
               'contracts assert'.
        top_k: number of matches to return (default 5).

    Returns:
        A list of dicts: {id, title, tier, category, score (0-100), path}.
        Empty list when the index is empty or the query is blank.
    """
    return _get_state().search(query, top_k)


@mcp.tool()
def compiler_status(paper_id: str, compiler: str | None = None) -> dict[str, Any]:
    """Look up compiler implementation status for a C++26 paper.

    INFORMATIONAL ONLY. The cpp26-adapter suggestion path is compiler-agnostic
    by design — the model must not gate recommendations on this. Use it for
    classifying review diagnostics as bug-vs-compiler-lag, never for choosing
    which idiom to write.

    Args:
        paper_id: WG21 paper id (e.g. 'P2996').
        compiler: optional compiler key — 'clang-22', 'clang-p2996',
                  'gcc-16', 'msvc-19.40'. When omitted, returns status for
                  every known compiler.

    Returns:
        A dict containing at minimum {paper_id, informational_only: True}.
        For known entries: {support, note, version, ...} (schema depends on
        corpus/status.yaml). For unknown paper or compiler: {support:
        'unknown', note: ...}.
    """
    return _get_state().compiler_status(paper_id, compiler)


def main() -> None:
    """Run the cpp26-ref MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
