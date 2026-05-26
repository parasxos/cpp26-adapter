#!/usr/bin/env bash
# Quarterly refresh entry point for cpp26-adapter.
#
# Runs:
#   1. corpus/scripts/fetch_index.py    — pull adopted-since-last-run
#                                          C++26 papers; diff against
#                                          current index.yaml.
#   2. corpus/scripts/refresh_status.py — scrape upstream cxx-status
#                                          pages; print a hand-mergeable
#                                          diff.
#   3. tools/validate_corpus.py         — schema + xref + syntax pass.
#
# Optional (--with-eval):
#   4. eval/run.py                       — full 39-task suite.
#                                          Expensive; only run when API
#                                          credits are available.
#
# Output: a docs/MAINTENANCE.md checklist describing the changes to merge.
# This script does NOT write to corpus/ — the operator commits manually
# after reviewing the diff.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV_PY="$ROOT/mcp-server/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "error: $VENV_PY not found. Run 'pip install -e mcp-server' first." >&2
    exit 1
fi

WITH_EVAL=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-eval) WITH_EVAL=1; shift;;
        --help|-h)
            sed -n '1,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//'
            exit 0;;
        *) echo "unknown arg: $1" >&2; exit 1;;
    esac
done

stamp() { date -u '+%Y-%m-%d %H:%M:%SZ'; }

echo "==> refresh.sh starting at $(stamp)"

echo
echo "===== step 1/3: fetch_index — adopted C++26 papers ====="
$VENV_PY corpus/scripts/fetch_index.py 2>&1 | tee /tmp/cpp26-refresh-fetch.log
fetch_rc=${PIPESTATUS[0]}

echo
echo "===== step 2/3: refresh_status — compiler implementation deltas ====="
$VENV_PY corpus/scripts/refresh_status.py 2>&1 | tee /tmp/cpp26-refresh-status.log
status_rc=${PIPESTATUS[0]}

echo
echo "===== step 3/3: validate_corpus — schema + xref + syntax ====="
$VENV_PY tools/validate_corpus.py 2>&1 | tee /tmp/cpp26-refresh-validate.log
validate_rc=${PIPESTATUS[0]}

if (( WITH_EVAL )); then
    echo
    echo "===== step 4 (opt): eval/run.py — full suite ====="
    $VENV_PY eval/run.py 2>&1 | tee /tmp/cpp26-refresh-eval.log || true
fi

echo
echo "==> refresh.sh finished at $(stamp)"
echo
echo "Step results: fetch_index=$fetch_rc  refresh_status=$status_rc  validate=$validate_rc"
echo
echo "Next steps (manual):"
echo "  1. Review the index.yaml diff (git diff corpus/index.yaml). Tier any new papers."
echo "  2. Review status.yaml against /tmp/cpp26-refresh-status.log; hand-merge changes."
echo "  3. If new deep papers were promoted, author corpus/references/<id>.md (or run gen_refs.py for shallow/stub)."
echo "  4. Commit and bump corpus version (header comment in index.yaml)."

exit 0
