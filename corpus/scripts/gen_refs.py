#!/usr/bin/env python3
"""Generate templated reference markdown for shallow and stub papers.

Deep-tier references are hand-authored; this script never touches them
(it skips rows where index.yaml says `tier: deep` and also skips any
existing reference file regardless of tier, so reruns are safe).

Shallow refs get a richer template (problem framing + TODO markers for
canonical example, pre-C++26 equivalent, gotchas). Stubs get a
1-sentence summary plus the canonical URL. Both have frontmatter with
heuristically-extracted keywords (title tokens minus stopwords,
augmented with category-derived synonyms).

Run:
    mcp-server/.venv/bin/python corpus/scripts/gen_refs.py
    # add --force to overwrite existing non-deep refs
    # add --only PFIX001,PFIX002 to target specific ids
    # add --tier shallow to only handle one tier
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.yaml"
REFS_DIR = ROOT / "references"

# Title tokens we drop when synthesising keywords.
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "for", "to", "in", "on", "by",
    "with", "as", "from", "is", "be", "are", "this", "that", "these",
    "into", "via", "use", "using", "should", "make", "support", "supports",
    "c++", "c++26", "c++23", "c++20", "lwg", "cwg", "ewg", "lewg",
    "draft", "wording", "wording-only", "design", "proposed", "proposal",
    "language", "library", "standard", "stl",
})

# Category-derived synonym tokens. Helps the MCP search match queries
# that use the colloquial term rather than the paper-title wording.
CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "reflection":  ["introspection", "metaprogramming", "std::meta"],
    "contracts":   ["assertion", "precondition", "postcondition"],
    "concurrency": ["async", "thread", "parallel", "atomic", "concurrent"],
    "coroutines":  ["coroutine", "co_await", "co_yield"],
    "modules":     ["module", "import", "export"],
    "ranges":      ["range", "view", "pipe"],
    "concepts":    ["concept", "requires", "constraint"],
    "numerics":    ["numeric", "math", "computation"],
    "library":     ["std", "stl"],
    "core":        ["language", "syntax"],
}

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_+]*")


def extract_keywords(title: str, category: str, paper_id: str) -> list[str]:
    """Heuristic keyword set: tokenise title + add category synonyms + paper id."""
    tokens = [w.lower() for w in WORD_RE.findall(title)]
    significant = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    extras = CATEGORY_SYNONYMS.get(category, [])
    # Preserve order, dedupe.
    seen: dict[str, None] = {}
    for t in (*significant, *extras, paper_id.lower()):
        seen.setdefault(t, None)
    return list(seen.keys())[:10]


def yaml_dump_frontmatter(row: dict, keywords: list[str]) -> str:
    front = {
        "id": row["id"],
        "title": row.get("title", ""),
        "revision": row.get("revision"),
        "tier": row.get("tier", "stub"),
        "category": row.get("category", "other"),
        "keywords": keywords,
        "canonical_url": row.get("canonical_url", ""),
    }
    return yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip()


SHALLOW_BODY = """## Summary
Adopted into C++26 at the {meeting} meeting.
{title_sentence}
Full paper: <{canonical_url}>.

## Idiom shift
- **Pre-C++26 path:** *TODO — hand-fill from paper context.*
- **C++26 path:** *TODO — add a minimal canonical example.*

## Gotchas
*TODO — note any implementation caveats once the compilers stabilise.*

## Related
*TODO — cross-reference adjacent papers in this category.*
"""


STUB_BODY = """*Stub — auto-extracted from `index.yaml`.* Adopted in C++26 at the
{meeting} meeting. Full paper text at <{canonical_url}>.
"""


def title_sentence(title: str) -> str:
    """Compose a short, neutral sentence describing the paper from its title.

    Avoids over-claiming when the title is terse — we just echo it back as
    a sentence the model can use as a grounding hint rather than invent
    semantics we don't know.
    """
    if not title:
        return ""
    bare = title.rstrip(".")
    if bare.lower().startswith(("why ", "make ", "fix ", "add ", "remove ", "introduce ")):
        return bare + "."
    return f"Adds **{bare}** to the standard."


def make_body(row: dict) -> str:
    tier = row.get("tier", "stub")
    if tier == "shallow":
        return SHALLOW_BODY.format(
            meeting=row.get("meeting", "unknown"),
            title_sentence=title_sentence(row.get("title", "")),
            canonical_url=row.get("canonical_url", ""),
        )
    return STUB_BODY.format(
        meeting=row.get("meeting", "unknown"),
        canonical_url=row.get("canonical_url", ""),
    )


def render(row: dict) -> str:
    keywords = extract_keywords(
        row.get("title", ""),
        row.get("category", "other"),
        row["id"],
    )
    fm = yaml_dump_frontmatter(row, keywords)
    heading = f"# {row['id']} — {row.get('title', '').strip()}"
    body = make_body(row)
    return f"---\n{fm}\n---\n\n{heading}\n\n{body}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing non-deep reference files",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated paper ids to generate (default: all shallow + stub)",
    )
    parser.add_argument(
        "--tier", choices=["shallow", "stub"],
        help="Only generate one tier",
    )
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"error: {INDEX_PATH} missing; run fetch_index.py first", file=sys.stderr)
        return 1

    rows = yaml.safe_load(INDEX_PATH.read_text())
    REFS_DIR.mkdir(parents=True, exist_ok=True)

    only_set: set[str] | None = None
    if args.only:
        only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    targets = [r for r in rows if r.get("tier") in ("shallow", "stub")]
    if args.tier:
        targets = [r for r in targets if r["tier"] == args.tier]
    if only_set:
        targets = [r for r in targets if r["id"] in only_set]

    print(f"target rows: {len(targets)} (force={args.force})", file=sys.stderr)

    wrote = 0
    skipped_existing = 0
    skipped_deep = 0
    for row in targets:
        pid = row["id"]
        path = REFS_DIR / f"{pid}.md"
        if path.exists() and not args.force:
            skipped_existing += 1
            continue
        content = render(row)
        path.write_text(content)
        wrote += 1

    # Sanity: report how many deep refs we left alone.
    skipped_deep = sum(1 for r in rows if r.get("tier") == "deep")

    print(
        f"wrote={wrote}  skipped(existing)={skipped_existing}  "
        f"deep-left-alone={skipped_deep}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
