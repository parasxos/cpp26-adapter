#!/usr/bin/env python3
"""Build `corpus/index.yaml` from `cplusplus/papers` GitHub issues.

Filter: `label:C++26 AND label:plenary-approved` — i.e. papers that landed
in the C++26 working draft. Title parsing extracts `(paper_id, revision,
short_title)`. Tier is seeded from a curated deep-tier list (see
`DEEP_TIER`); topic labels (reflection, contracts, senders/receivers, …)
promote to `shallow`; everything else is `stub`. The heuristic is meant
as a starting point — manually retier rows in `corpus/index.yaml`
afterwards; the script will not clobber unrecognised rows on rerun
because it overwrites the whole file. Re-tiering manually means editing
the YAML directly, not re-running the script.

Requirements:
  - `gh` CLI on PATH and authenticated (`gh auth status`).
  - Python with `pyyaml` available — easiest via the mcp-server venv:
      mcp-server/.venv/bin/python corpus/scripts/fetch_index.py

Notes on GitHub search:
  - The `search/issues` endpoint caps results at 1000; C++26 currently has
    ~215 plenary-approved issues, so paging is straightforward.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = "cplusplus/papers"

# Curated deep tier — papers that warrant a hand-written reference.
# Sourced from PLAN.md §1c. Each entry is a ~2.5-hour authoring commitment;
# add to this set deliberately.
DEEP_TIER: frozenset[str] = frozenset({
    "P2996",  # Reflection for C++26
    "P2900",  # Contracts
    "P2300",  # std::execution (senders/receivers)
    "P1306",  # Expansion statements (template for)
    "P2662",  # Pack indexing
    "P2573",  # = delete("reason")
    "P2893",  # Variadic friends
    "P1967",  # #embed
    "P2795",  # Erroneous behaviour
    "P1673",  # std::linalg
    "P2530",  # Hazard pointers (PLAN.md listed P1121 which is Concurrency TS-2)
    "P2545",  # Read-copy-update (RCU)
    "P3471",  # Standard library hardening
    "P3068",  # Throwing exceptions in constant evaluation
    # NOTE: PLAN.md seed listed P1938 (if consteval), but that landed in C++23
    # — not C++26. Dropped.
    "P2169",  # A nice placeholder with no name
    "P0843",  # inplace_vector
})

# Topic labels that promote a paper to shallow tier.
SHALLOW_PROMOTERS: frozenset[str] = frozenset({
    "reflection", "contracts", "senders/receivers", "concurrency",
    "modules", "coroutines", "ranges", "concepts", "constexpr",
    "format", "numerics", "freestanding", "linear-algebra",
    "modular-standard-library", "profiles", "noexcept",
    "modules-ecosystem-tr-1", "senders/receivers",
})

# Category buckets, in priority order. First matching label wins.
CATEGORY_RULES: list[tuple[str, str]] = [
    ("reflection",        "reflection"),
    ("contracts",         "contracts"),
    ("senders/receivers", "concurrency"),
    ("concurrency",       "concurrency"),
    ("coroutines",        "coroutines"),
    ("modules",           "modules"),
    ("ranges",            "ranges"),
    ("concepts",          "concepts"),
    ("linear-algebra",    "numerics"),
    ("numerics",          "numerics"),
    ("format",            "library"),
    ("constexpr",         "core"),
    ("freestanding",      "library"),
    ("LWG",               "library"),
    ("LEWG",              "library"),
    ("CWG",               "core"),
    ("EWG",               "core"),
]

TITLE_RE = re.compile(r"^(P\d{4})(?:\s+R(\d+))?\s+(.+?)\s*$")

# Two queries, unioned by issue number:
#   A: explicit C++26 label + plenary-approved (the primary path).
#   B: plenary-approved + IS, excluding other versions/TS — catches papers
#      that landed in the C++26 working draft without an explicit C++26
#      label (e.g. P0952, P3372, P3378 as of 2026-05).
QUERY_A = "repo:cplusplus/papers+label:%22C%2B%2B26%22+label:plenary-approved"
QUERY_B = (
    "repo:cplusplus/papers+label:plenary-approved+label:IS"
    "+-label:%22C%2B%2B23%22+-label:%22C%2B%2B29%22+-label:%22C%2B%2B20%22+-label:TS"
)


def gh_api(path: str) -> list[dict]:
    """Page through a search endpoint via gh CLI."""
    out: list[dict] = []
    page = 1
    while True:
        cmd = ["gh", "api", f"{path}&page={page}&per_page=100"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        chunk = json.loads(result.stdout)
        items = chunk.get("items") if isinstance(chunk, dict) else chunk
        if not items:
            break
        out.extend(items)
        if len(items) < 100:
            break
        page += 1
        if page > 11:
            raise RuntimeError("search/issues 1000-result limit reached; revise query")
    return out


def parse_title(title: str) -> tuple[str, str | None, str] | None:
    """Extract (paper_id, revision_or_None, short_title) from an issue title.

    Some issue titles omit the `Rx` revision (e.g., "P2545 Why RCU Should be
    in C++26") — revision is None in that case; downstream falls back to the
    bare paper_id when building wg21.link URLs.
    """
    m = TITLE_RE.match(title)
    if m is None:
        return None
    revision = f"R{m.group(2)}" if m.group(2) else None
    return m.group(1), revision, m.group(3)


def assign_tier(paper_id: str, labels: set[str]) -> str:
    if paper_id in DEEP_TIER:
        return "deep"
    if labels & SHALLOW_PROMOTERS:
        return "shallow"
    return "stub"


def assign_category(labels: set[str]) -> str:
    for label, category in CATEGORY_RULES:
        if label in labels:
            return category
    return "other"


def main() -> int:
    if not shutil.which("gh"):
        print("error: gh CLI not found; install from https://cli.github.com/", file=sys.stderr)
        return 1

    raw_a = gh_api(f"search/issues?q={QUERY_A}")
    raw_b = gh_api(f"search/issues?q={QUERY_B}")
    by_num: dict[int, dict] = {x["number"]: x for x in raw_a}
    for x in raw_b:
        by_num.setdefault(x["number"], x)
    raw = list(by_num.values())
    print(
        f"fetched {len(raw_a)} (A) + {len(raw_b)} (B) → {len(raw)} unique issues",
        file=sys.stderr,
    )

    rows: list[dict] = []
    skipped: list[tuple[int, str]] = []
    for issue in raw:
        parsed = parse_title(issue["title"])
        if parsed is None:
            skipped.append((issue["number"], issue["title"]))
            continue
        paper_id, revision, short_title = parsed
        labels = {l["name"] for l in issue["labels"]}
        rows.append({
            "id": paper_id,
            "title": short_title,
            "revision": revision,
            "meeting": (issue.get("milestone") or {}).get("title", "unknown"),
            "tier": assign_tier(paper_id, labels),
            "category": assign_category(labels),
            "ref": f"references/{paper_id}.md",
            "canonical_url": f"https://wg21.link/{paper_id}{revision or ''}",
            "issue_url": issue["html_url"],
        })

    # Deduplicate by paper id — keep the highest revision (None counts as -1).
    def rev_num(r: dict) -> int:
        return int(r["revision"][1:]) if r["revision"] else -1

    by_id: dict[str, dict] = {}
    for row in rows:
        existing = by_id.get(row["id"])
        if existing is None or rev_num(row) > rev_num(existing):
            by_id[row["id"]] = row
    rows = sorted(by_id.values(), key=lambda r: r["id"])

    tier_counts: dict[str, int] = {"deep": 0, "shallow": 0, "stub": 0}
    for r in rows:
        tier_counts[r["tier"]] += 1
    print(
        f"deep={tier_counts['deep']} shallow={tier_counts['shallow']} "
        f"stub={tier_counts['stub']} total={len(rows)}",
        file=sys.stderr,
    )

    # Warn about deep-tier entries from the curated list that did not appear
    # in the fetched set (typo, paper not yet plenary-approved, etc.).
    fetched_ids = {r["id"] for r in rows}
    missing_deep = sorted(DEEP_TIER - fetched_ids)
    if missing_deep:
        print(
            f"warning: deep-tier seed entries not found in fetch: {missing_deep}",
            file=sys.stderr,
        )

    if skipped:
        print(f"skipped {len(skipped)} issues whose title did not match Pxxxx Ry pattern:", file=sys.stderr)
        for num, title in skipped[:10]:
            print(f"  #{num}: {title!r}", file=sys.stderr)

    out_path = Path(__file__).resolve().parent.parent / "index.yaml"
    header = (
        "# Master index of C++26 papers.\n"
        f"# Generated by corpus/scripts/fetch_index.py from {REPO}.\n"
        "# Filter: label:C++26 AND label:plenary-approved.\n"
        "#\n"
        "# Tier: 'deep' = hand-curated reference (~2.5 hr/paper);\n"
        "#       'shallow' = LLM-assisted summary + canonical example (~25 min);\n"
        "#       'stub' = auto-extracted title + 1-sentence summary (~5 min).\n"
        "# Edit DEEP_TIER in fetch_index.py to promote a paper to deep.\n"
        "# Re-tier individual rows by editing this file directly — script reruns overwrite it.\n"
        "\n"
    )
    out_path.write_text(header + yaml.safe_dump(rows, sort_keys=False, allow_unicode=True))
    print(f"wrote {out_path} ({len(rows)} papers)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
