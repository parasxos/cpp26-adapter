#!/usr/bin/env python3
"""Pass-1 regex anti-pattern check for the cpp26-reviewer subagent.

Reads patterns from `patterns.yaml` (sibling), scans each input file
line-by-line, and emits findings as JSON to stdout.

Output shape:
  [
    {
      "file": "<path>",
      "line": <int, 1-based>,
      "match": "<line content, truncated>",
      "pattern": "<the regex that matched>",
      "suggest": "<remediation hint>",
      "paper": "<WG21 id or ''>",
      "severity": "warning" | "info"
    }, ...
  ]

Usage:
    quick_lint.py FILE [FILE...]                          # JSON to stdout
    quick_lint.py --compact FILE [FILE...]                # human-readable
    quick_lint.py --severity warning FILE [FILE...]       # filter
    echo /tmp/x.cpp | CLAUDE_HOOK_INPUT=$(cat) quick_lint.py   # hook mode

Exit code is always 0 — findings are data, not errors. The reviewer
agent (or the PostToolUse hook surface) decides how to act on them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PATTERNS_PATH = Path(__file__).resolve().parent / "patterns.yaml"

SEVERITY_RANK = {"warning": 1, "info": 2}


def load_patterns() -> list[dict[str, Any]]:
    raw = yaml.safe_load(PATTERNS_PATH.read_text()) or []
    out: list[dict[str, Any]] = []
    for entry in raw:
        try:
            entry["_compiled"] = re.compile(entry["pattern"])
        except re.error as e:
            print(f"warning: skipping bad pattern {entry.get('pattern')!r}: {e}",
                  file=sys.stderr)
            continue
        out.append(entry)
    return out


def lint_file(path: Path, patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        text = path.read_text(errors="replace")
    except OSError as e:
        return [{"file": str(path), "error": f"could not read: {e}"}]
    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for p in patterns:
            if p["_compiled"].search(line):
                findings.append({
                    "file": str(path),
                    "line": line_no,
                    "match": line.strip()[:120],
                    "pattern": p["pattern"],
                    "suggest": p.get("suggest", ""),
                    "paper": p.get("paper", ""),
                    "severity": p.get("severity", "warning"),
                })
    return findings


def files_from_args_or_env(args_files: list[str]) -> list[str]:
    if args_files:
        return args_files
    # Hooks set CLAUDE_HOOK_INPUT — for Edit/Write tools this includes the
    # affected file path. Be lenient about parsing — accept any whitespace-
    # separated tokens that look like file paths.
    raw = os.environ.get("CLAUDE_HOOK_INPUT", "")
    if not raw:
        return []
    return [tok for tok in raw.split() if Path(tok).exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C++26 anti-pattern Pass-1 lint")
    parser.add_argument("files", nargs="*", help="files to lint")
    parser.add_argument("--compact", action="store_true",
                        help="emit one-line-per-finding human text instead of JSON")
    parser.add_argument("--severity", choices=("warning", "info"),
                        help="filter findings to this severity and above")
    args = parser.parse_args(argv)

    files = files_from_args_or_env(args.files)
    if not files:
        # Silent success: nothing to lint (e.g. hook fired with non-cpp path).
        print("[]" if not args.compact else "", end="")
        return 0

    patterns = load_patterns()
    findings: list[dict[str, Any]] = []
    for f in files:
        findings.extend(lint_file(Path(f), patterns))

    if args.severity:
        cutoff = SEVERITY_RANK[args.severity]
        findings = [
            f for f in findings
            if SEVERITY_RANK.get(f.get("severity", "info"), 99) <= cutoff
        ]

    if args.compact:
        for f in findings:
            paper = f.get("paper") or "?"
            print(f"  {f.get('file', '?')}:{f.get('line', '?')}: "
                  f"[{f.get('severity', 'warning')}] {f.get('suggest', '')} ({paper})")
    else:
        json.dump(findings, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
