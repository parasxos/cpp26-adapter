#!/usr/bin/env python3
"""Diff `corpus/status.yaml` against upstream compiler cxx-status pages.

This script does NOT auto-write changes. It prints a unified-diff-like
summary of what differs between the current `status.yaml` and freshly
scraped data, so the operator can decide which updates to accept.

Sources scraped (best-effort; the formats change occasionally):
  - https://clang.llvm.org/cxx_status.html#cxx26
  - https://gcc.gnu.org/projects/cxx-status.html#cxx26
  - https://learn.microsoft.com/en-us/cpp/overview/visual-cpp-language-conformance
  - https://github.com/bloomberg/clang-p2996  (README parse)

Run quarterly. The output is a checklist for the human; copy-paste the
relevant entries back into status.yaml manually.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = ROOT / "status.yaml"

SOURCES = {
    "clang":    "https://clang.llvm.org/cxx_status.html",
    "gcc":      "https://gcc.gnu.org/projects/cxx-status.html",
    "msvc":     "https://learn.microsoft.com/en-us/cpp/overview/visual-cpp-language-conformance",
    "p2996":    "https://raw.githubusercontent.com/bloomberg/clang-p2996/main/README.md",
}

USER_AGENT = "cpp26-adapter/refresh_status (parasxos@gmail.com)"


def fetch(url: str) -> str:
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError, OSError) as e:
        return f"<fetch-error: {e}>"


def grep_paper(html: str, paper_id: str) -> list[str]:
    """Pull lines mentioning the paper id (case-insensitive).

    The cxx-status pages are HTML tables; without parsing the table
    structure we still get a useful "is this paper mentioned and what
    surrounds it" view by grepping raw text.
    """
    needle = paper_id.lower()
    hits = []
    for line in html.splitlines():
        if needle in line.lower():
            stripped = " ".join(line.split())
            if 0 < len(stripped) < 250:
                hits.append(stripped)
    return hits[:5]


def main() -> int:
    if not STATUS_PATH.exists():
        print(f"error: {STATUS_PATH} missing", file=sys.stderr)
        return 1

    status = yaml.safe_load(STATUS_PATH.read_text())
    if not isinstance(status, dict):
        print("error: malformed status.yaml", file=sys.stderr)
        return 1

    papers = sorted(k for k in status.keys() if k.startswith("P"))
    print(f"refresh_status — {len(papers)} deep-tier papers in status.yaml")
    print(f"last_refreshed: {status.get('last_refreshed', '<missing>')}")
    print(f"running at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print()

    pages: dict[str, str] = {}
    for tag, url in SOURCES.items():
        print(f"fetching {tag}: {url}", file=sys.stderr)
        pages[tag] = fetch(url)

    print()
    print("Per-paper findings (manual review needed — script does NOT write).")
    print("=" * 72)
    for paper in papers:
        print(f"\n## {paper}  (current entries: {sorted(status[paper].keys())})")
        for tag, page in pages.items():
            hits = grep_paper(page, paper)
            if not hits:
                continue
            print(f"  [{tag}]")
            for h in hits[:3]:
                print(f"    {h[:200]}")

    print()
    print("Next step: hand-merge any new mentions back into status.yaml,")
    print("bump `last_refreshed`, and commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
