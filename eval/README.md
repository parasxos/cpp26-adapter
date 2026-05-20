# cpp26-adapter eval

The Phase-7 evaluation harness for the binding plan's DoD gate:
**≥85% standard compliance** on a 39-task held suite.

## Files

- `tasks.yaml` — 39 tasks across the 16 deep-tier C++26 features
  (≥1 per paper, ≥1 per category). Each task has a prompt phrased to
  *avoid* naming C++26 — we measure whether the model reaches for the
  idiom unprompted.
- `run.py` — 3-axis harness. Invokes `claude -p` twice per task (with
  and without the plugin) and scores each output against:
    1. Standard compliance (binary, regex must_contain / must_not_contain)
    2. Syntactic correctness (binary, `clang -std=c++2c -fsyntax-only`)
    3. Idiomatic quality (1-5, LLM-judge via a second `claude -p` call)
- `results-vX.Y.md` — generated per run (gitignored).

## How to run

```bash
# Full 39-task suite (~60-90 minutes, ~$15-25 in API calls).
mcp-server/.venv/bin/python eval/run.py

# Smoke test (first 3 tasks, no judge).
mcp-server/.venv/bin/python eval/run.py --tasks 3 --skip-judge

# One task by id.
mcp-server/.venv/bin/python eval/run.py --only enum-to-string

# Drop axis 2 (when the local clang is below the C++26 baseline).
mcp-server/.venv/bin/python eval/run.py --skip-syntax

# Drop axis 3 (saves judge tokens).
mcp-server/.venv/bin/python eval/run.py --skip-judge
```

## Token budget

Each task is 2 `claude -p` calls (plugin off + on) plus 1 optional
judge call. Budget ~$0.05-$0.20 per call; full suite ~$15-25. The
harness streams output to stderr so you can interrupt with `^C` and
get a partial report.

## Acceptance

Output `results-vX.Y.md` must show **axis-1 ≥ 85%** for the plugin-on
column. Axis 2 is informational below the clang-22 baseline. Axis 3
should show a meaningful delta vs plugin-off (median ≥4/5 with plugin
on; baseline typically 2-3).

## When the gate fails

The binding plan §7c iteration playbook:

1. Identify systematic failures — group failing tasks by paper.
2. Strengthen `skills/cpp26-idioms/SKILL.md`'s decision table for the
   failing rows (richer entry, more keywords, sharper anti-pattern).
3. Add anti-pattern regexes to `tools/cpp26_lint/patterns.yaml` if
   the failure mode is deterministically catchable.
4. Tighten the skill's `description:` frontmatter — activation is
   description-matched, not body-matched.
5. Last resort: PostToolUse hook that auto-prepends a steering note
   when an anti-pattern is detected mid-generation.
6. Re-run.
