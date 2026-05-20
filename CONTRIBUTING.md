# Contributing to cpp26-adapter

Bug reports, eval-task suggestions, and install confirmations are all
welcome. The repo carries the full build history (16 commits across
the 9 binding-plan phases), so reading [`PLAN.md`](PLAN.md) and the
commit log gives a clean picture of why every component exists.

## Quick paths

- **Just confirming the install works?**
  Use the [install confirmation](.github/ISSUE_TEMPLATE/install_works.md)
  template. It closes part of the v1.0 gate.

- **Spot a wrong suggestion or classification?**
  Use the [bug report](.github/ISSUE_TEMPLATE/bug.md) template — pick
  the classification (wrong suggestion / wrong reviewer classification
  / activation failure / MCP failure) so the maintainer can route fast.

- **Have a prompt that should pass and doesn't?**
  Open an [eval task suggestion](.github/ISSUE_TEMPLATE/eval_task_suggestion.md).
  The held suite at `eval/tasks.yaml` gates every release.

## Local development

```bash
git clone https://github.com/parasxos/cpp26-adapter.git
cd cpp26-adapter
python3 -m venv mcp-server/.venv
mcp-server/.venv/bin/pip install -e "mcp-server[dev]"

# Run the test suites
mcp-server/.venv/bin/pytest -q mcp-server/tests agents/tests

# Run the validator (schema + xref; syntax check needs clang ≥ 22)
mcp-server/.venv/bin/python tools/validate_corpus.py

# Load the plugin in a fresh Claude Code session
claude --plugin-dir .
```

## Running the eval

The 39-task held suite at `eval/tasks.yaml` gates every release.

```bash
# Smoke test (3 tasks, no judge, no baseline — verifies the harness)
mcp-server/.venv/bin/python eval/run.py --tasks 3 --skip-judge --no-off

# Full run (~50 min on subscription auth, ~$15-25 on API auth)
mcp-server/.venv/bin/python eval/run.py
```

By default the harness strips `ANTHROPIC_API_KEY` from the subprocess
env so `claude -p` uses your Claude subscription quota. Set
`CPP26_EVAL_USE_API=1` to opt back into per-token API billing.

The bar is **≥85% standard-compliance** (axis-1). v1.0 is gated on
two successive eval-passing refreshes per [`MAINTENANCE.md`](MAINTENANCE.md).

## Adding a new deep-tier reference

When a new C++26 paper warrants a hand-curated reference (e.g., a
late-DR feature that landed in the IS):

1. Add the paper id to `DEEP_TIER` in `corpus/scripts/fetch_index.py`.
2. Re-run `fetch_index.py` so the tier flips to `deep` in `index.yaml`.
3. Author `corpus/references/<id>.md` following the structure of any
   of the 16 existing deep refs (frontmatter + Problem + Key syntax
   + Canonical example + Pre-C++26 equivalent + Gotchas + Related).
4. Add the paper to `corpus/status.yaml` with at-least clang-22 /
   clang-p2996 / gcc-16 / msvc-19.40 entries.
5. Add a row to the SKILL.md decision table referencing the new ref.
6. Add 1+ task to `eval/tasks.yaml` exercising the canonical idiom.
7. Re-run validator + eval; commit.

The bookkeeping is captured in [`MAINTENANCE.md`](MAINTENANCE.md).

## Adding a new anti-pattern regex

When the eval surfaces a class of failures that's deterministically
catchable (the model keeps emitting `assert(` instead of
`contract_assert`, say), add a regex to
`tools/cpp26_lint/patterns.yaml`:

```yaml
- pattern: '\bassert\s*\('
  suggest: "use contract_assert(...)"
  paper: P2900
  severity: warning   # or info, info-only triggers if no warnings present
```

The regex is shared between the PostToolUse hook (surfaces findings
inline) and the cpp26-reviewer Pass 1 (classification).

## Coding conventions

- **Python**: 3.11+, type-hinted, ruff-clean. Line length 100.
- **C++ code in references / fixtures**: must be syntactically credible
  C++26. No made-up syntax (compile against `clang-p2996` or the
  current revision of P2996 if unsure).
- **Markdown**: GitHub-flavoured. Mermaid diagrams are fine (GitHub
  renders them). No raw HTML.
- **Commits**: imperative mood, prefixed with the phase or component
  where applicable (e.g. `Phase 4:` or `eval:`). Match the existing
  log style.

## License

Contributions are dual-licensed:
- Code (everything outside `corpus/`) under MIT.
- Knowledge corpus contributions under CC-BY-SA-4.0.

By submitting a PR you assert you have the right to license your
contribution under these terms.
