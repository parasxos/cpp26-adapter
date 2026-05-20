#!/usr/bin/env python3
"""Validate the C++26 corpus.

Three passes:
  1. **Schema** — every `references/*.md` has YAML frontmatter with at
     least `id`, `title`, `tier`. Tier must be 'deep' | 'shallow' | 'stub'.
  2. **Cross-reference** — every `corpus/index.yaml` row has a matching
     reference file; no orphan reference files exist.
  3. **Deep-tier syntax** — extract fenced ```cpp``` blocks from deep
     references, write each to a temp file, run
     `clang -std=c++2c -fsyntax-only` and classify the result as
     PASS / SKIP (compiler lacks feature support per status.yaml) /
     FAIL (compiler claims support, snippet errored).

Exit code:
  0 — schema clean, no orphans, no deep snippet hard-failed
  1 — schema/orphan errors (always blocking)
  2 — deep snippet hard-failed (only under --strict)

Usage:
    mcp-server/.venv/bin/python tools/validate_corpus.py
    # add --strict to make snippet failures non-zero
    # add --no-syntax-check to skip Pass 3 (CI without C++ toolchain)
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "corpus" / "index.yaml"
STATUS_PATH = ROOT / "corpus" / "status.yaml"
REFS_DIR = ROOT / "corpus" / "references"

REQUIRED_FRONT_KEYS = {"id", "title", "tier"}
ALLOWED_TIERS = {"deep", "shallow", "stub"}

CPP_BLOCK_RE = re.compile(r"```cpp\n(.*?)\n```", re.DOTALL)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        loaded = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def pass1_schema(refs_dir: Path) -> list[str]:
    """Schema-check every reference file. Returns a list of errors."""
    errors: list[str] = []
    for md_path in sorted(refs_dir.glob("*.md")):
        text = md_path.read_text(errors="replace")
        front = parse_frontmatter(text)
        if front is None:
            errors.append(f"{md_path.name}: missing or unparseable YAML frontmatter")
            continue
        missing = REQUIRED_FRONT_KEYS - front.keys()
        if missing:
            errors.append(f"{md_path.name}: frontmatter missing keys: {sorted(missing)}")
        tier = front.get("tier")
        if tier not in ALLOWED_TIERS:
            errors.append(f"{md_path.name}: tier {tier!r} not in {sorted(ALLOWED_TIERS)}")
        # ID must match the filename for the MCP to find it.
        pid = front.get("id")
        if pid and pid != md_path.stem:
            errors.append(f"{md_path.name}: frontmatter id={pid!r} != filename stem {md_path.stem!r}")
    return errors


def pass2_xref(index_path: Path, refs_dir: Path) -> list[str]:
    """Cross-check index.yaml ids against references/ files."""
    errors: list[str] = []
    if not index_path.exists():
        return [f"{index_path}: missing"]
    rows = yaml.safe_load(index_path.read_text()) or []
    index_ids = {row.get("id") for row in rows if row.get("id")}
    ref_ids = {p.stem for p in refs_dir.glob("*.md")}
    for missing in sorted(index_ids - ref_ids):
        errors.append(f"index row {missing} has no reference file")
    for orphan in sorted(ref_ids - index_ids):
        errors.append(f"reference {orphan}.md is not in index.yaml (orphan)")
    return errors


def _probe_clang_baseline(clang: str) -> tuple[bool, str]:
    """Return (meets_c++26_baseline, reason).

    Apple clang versions track Xcode and lag mainline; treat them as
    below-baseline regardless of the major number. For mainline clang,
    require major >= 22 per PLAN.md.
    """
    raw = subprocess.run(
        [clang, "--version"], capture_output=True, text=True
    ).stdout.splitlines()[0] if clang else ""
    if not raw:
        return False, "could not read clang --version"
    if "Apple" in raw:
        return False, f"Apple clang ({raw}) — does not track mainline; reflection/template-for unsupported"
    m = re.search(r"version (\d+)", raw)
    if not m:
        return False, f"could not parse version from {raw!r}"
    major = int(m.group(1))
    if major < 22:
        return False, f"clang {major} (below 22 baseline)"
    return True, raw


def pass3_syntax(refs_dir: Path, status: dict[str, Any], clang: str | None) -> dict[str, list[str]]:
    """Try compiling each cpp block from deep refs. Returns counts + details."""
    results: dict[str, list[str]] = {"PASS": [], "SKIP": [], "FAIL": []}
    if clang is None:
        return results

    # Probe clang once: does it accept -std=c++2c at all?
    probe = subprocess.run(
        [clang, "-std=c++2c", "-x", "c++", "-E", "-"],
        input="int main() { return 0; }\n",
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        # No -std=c++2c support → skip everything.
        return {"PASS": [], "SKIP": ["compiler does not accept -std=c++2c"], "FAIL": []}

    meets_baseline, baseline_reason = _probe_clang_baseline(clang)
    if not meets_baseline:
        # Add the reason as a single SKIP entry so the user sees why all the
        # deep snippets are not real-tested.
        results["SKIP"].append(f"local toolchain below C++26 baseline: {baseline_reason}")

    for md_path in sorted(refs_dir.glob("*.md")):
        text = md_path.read_text(errors="replace")
        front = parse_frontmatter(text) or {}
        if front.get("tier") != "deep":
            continue
        paper_id = front.get("id", md_path.stem)
        compiler_support = (status.get(paper_id) or {}).get("clang-22", {}).get("support", "unknown")

        blocks = CPP_BLOCK_RE.findall(text)
        for i, block in enumerate(blocks):
            with tempfile.NamedTemporaryFile(
                suffix=".cpp", mode="w", delete=False
            ) as tf:
                tf.write(block)
                tf_path = Path(tf.name)
            try:
                r = subprocess.run(
                    [clang, "-std=c++2c", "-fsyntax-only", "-Wno-everything", str(tf_path)],
                    capture_output=True, text=True, timeout=30,
                )
                if r.returncode == 0:
                    results["PASS"].append(f"{md_path.name}#block{i}")
                elif not meets_baseline:
                    # Local clang is below the C++26 baseline; treat failures
                    # as expected toolchain-lag, never as a corpus defect.
                    results["SKIP"].append(
                        f"{md_path.name}#block{i} (paper={paper_id}; local toolchain below baseline)"
                    )
                elif compiler_support in ("none", "partial", "unknown"):
                    results["SKIP"].append(
                        f"{md_path.name}#block{i} (paper={paper_id} clang-22={compiler_support})"
                    )
                else:
                    results["FAIL"].append(
                        f"{md_path.name}#block{i} (paper={paper_id} clang-22={compiler_support}): "
                        f"{r.stderr.splitlines()[0] if r.stderr else 'no diagnostic'}"
                    )
            finally:
                tf_path.unlink(missing_ok=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 on Pass-3 hard failures")
    parser.add_argument("--no-syntax-check", action="store_true",
                        help="skip Pass 3 (use in CI without a C++ toolchain)")
    args = parser.parse_args()

    print(f"validate_corpus — references at {REFS_DIR}")

    p1 = pass1_schema(REFS_DIR)
    print(f"\nPass 1 — schema: {'CLEAN' if not p1 else f'{len(p1)} errors'}")
    for e in p1:
        print(f"  • {e}")

    p2 = pass2_xref(INDEX_PATH, REFS_DIR)
    print(f"\nPass 2 — index ↔ refs: {'CLEAN' if not p2 else f'{len(p2)} errors'}")
    for e in p2:
        print(f"  • {e}")

    blocking = len(p1) + len(p2) > 0

    p3: dict[str, list[str]] = {"PASS": [], "SKIP": [], "FAIL": []}
    if not args.no_syntax_check:
        status = yaml.safe_load(STATUS_PATH.read_text()) if STATUS_PATH.exists() else {}
        clang = shutil.which("clang") or shutil.which("clang++")
        print(f"\nPass 3 — deep-tier syntax: clang={clang or '<not found>'}")
        p3 = pass3_syntax(REFS_DIR, status if isinstance(status, dict) else {}, clang)
        print(f"  PASS={len(p3['PASS'])}  SKIP={len(p3['SKIP'])}  FAIL={len(p3['FAIL'])}")
        for label in ("FAIL", "SKIP"):
            for entry in p3[label][:10]:
                print(f"  [{label}] {entry}")
            if len(p3[label]) > 10:
                print(f"  [{label}] ... ({len(p3[label]) - 10} more)")

    if blocking:
        return 1
    if args.strict and p3["FAIL"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
