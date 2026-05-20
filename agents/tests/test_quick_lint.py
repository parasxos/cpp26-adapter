"""Test harness for the cpp26-reviewer Pass-1 regex check.

For each fixture under `fixtures/`, run `tools/cpp26_lint/quick_lint.py`,
parse the JSON output, and assert that the findings match the
`expected.yaml` contract.

Pass-2 (clang -fsyntax-only) is not exercised here — that path requires
clang 22+ which is not generally available on dev boxes. The reviewer
agent's Pass-2 logic is validated end-to-end during Phase 7 eval.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_PATH = FIXTURES_DIR / "expected.yaml"
LINT_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "cpp26_lint" / "quick_lint.py"


def _expected() -> dict[str, dict]:
    return yaml.safe_load(EXPECTED_PATH.read_text())


def _run_lint(fixture_path: Path) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(fixture_path)],
        capture_output=True, text=True, check=True,
    )
    if not result.stdout.strip():
        return []
    return json.loads(result.stdout)


@pytest.mark.parametrize("fixture_name", sorted(_expected().keys()))
def test_fixture(fixture_name: str) -> None:
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"missing fixture {fixture_path}"

    expected = _expected()[fixture_name]
    findings = _run_lint(fixture_path)
    warnings = [f for f in findings if f.get("severity") == "warning"]

    if "warning_count" in expected:
        # Clean fixture: explicit zero (or N) warning count.
        assert len(warnings) == expected["warning_count"], (
            f"{fixture_name}: expected {expected['warning_count']} warnings, "
            f"got {len(warnings)}: {warnings}"
        )
    if "min_warnings" in expected:
        # Bad fixture: at least N warnings expected.
        assert len(warnings) >= expected["min_warnings"], (
            f"{fixture_name}: expected >= {expected['min_warnings']} warnings, "
            f"got {len(warnings)}: {warnings}"
        )
    if "expected_papers" in expected:
        seen_papers = {w["paper"] for w in warnings}
        for paper in expected["expected_papers"]:
            assert paper in seen_papers, (
                f"{fixture_name}: expected paper {paper} in findings; "
                f"saw {sorted(seen_papers)}"
            )
