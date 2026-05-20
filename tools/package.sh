#!/usr/bin/env bash
# Build a release tarball of the cpp26-adapter plugin.
#
# Steps:
#   1. Compute the release directory (../cpp26-adapter-<version>).
#   2. Stage a clean copy excluding dev artefacts (.git, .venv, raw cache).
#   3. Replace skills/cpp26-idioms/references symlink with a real copy
#      (the symlink works in-tree for dev; release tarballs need files).
#   4. Tar + report install size; fail loudly if >5 MB (binding plan §6).
#
# Run from the repo root:
#   tools/package.sh                     # produce cpp26-adapter-0.9.0.tgz
#   tools/package.sh --output /tmp/x.tgz # custom output path
#
# This script does NOT publish anywhere. Distribution is Phase 8.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ----- read version from .claude-plugin/plugin.json -----
VERSION=$(python3 - <<'PY'
import json, sys
with open(".claude-plugin/plugin.json") as f:
    print(json.load(f)["version"])
PY
)

OUTPUT="${ROOT}/dist/cpp26-adapter-${VERSION}.tgz"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output) OUTPUT="$2"; shift 2;;
        *) printf 'unknown arg: %s\n' "$1" >&2; exit 1;;
    esac
done

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

STAGE="$WORK/cpp26-adapter"
mkdir -p "$STAGE"

echo "==> staging into $STAGE (version $VERSION)" >&2

# rsync is on macOS by default; --exclude is the cleanest way to drop dev artefacts.
rsync -a --delete \
    --exclude '.git/' \
    --exclude '*.venv/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache/' \
    --exclude '.mypy_cache/' \
    --exclude '.ruff_cache/' \
    --exclude 'corpus/raw/*.html' \
    --exclude 'corpus/raw/*.pdf' \
    --exclude 'corpus/raw/*.bs' \
    --exclude 'corpus/raw/*.bin' \
    --exclude 'corpus/raw/fetch_log.json' \
    --exclude 'dist/' \
    --exclude '.DS_Store' \
    "$ROOT/" "$STAGE/"

# ----- resolve symlink → real copy of references -----
SYMLINK="$STAGE/skills/cpp26-idioms/references"
if [[ -L "$SYMLINK" ]]; then
    echo "==> resolving symlink: skills/cpp26-idioms/references" >&2
    rm "$SYMLINK"
    cp -R "$ROOT/corpus/references" "$SYMLINK"
fi

# ----- size check -----
mkdir -p "$(dirname "$OUTPUT")"
tar -czf "$OUTPUT" -C "$WORK" cpp26-adapter
SIZE_BYTES=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT")
SIZE_KB=$(( SIZE_BYTES / 1024 ))
echo "==> wrote $OUTPUT (${SIZE_KB} KB)" >&2

if (( SIZE_KB > 5120 )); then
    echo "==> ERROR: tarball ${SIZE_KB} KB exceeds 5 MB budget (PLAN.md §6 acceptance)" >&2
    exit 1
fi

# ----- sanity: tarball contains expected entries -----
echo "==> verifying tarball contents" >&2
EXPECTED=(
    "cpp26-adapter/.claude-plugin/plugin.json"
    "cpp26-adapter/.mcp.json"
    "cpp26-adapter/skills/cpp26-idioms/SKILL.md"
    "cpp26-adapter/skills/cpp26-idioms/references/P2996.md"
    "cpp26-adapter/agents/cpp26-reviewer.md"
    "cpp26-adapter/commands/cpp26-init.md"
    "cpp26-adapter/hooks/hooks.json"
    "cpp26-adapter/mcp-server/src/cpp26_ref/server.py"
    "cpp26-adapter/corpus/index.yaml"
    "cpp26-adapter/corpus/status.yaml"
    "cpp26-adapter/tools/cpp26_lint/patterns.yaml"
)
missing=0
for entry in "${EXPECTED[@]}"; do
    if ! tar -tzf "$OUTPUT" | grep -qx "$entry"; then
        echo "  MISSING: $entry" >&2
        missing=$((missing+1))
    fi
done
if (( missing > 0 )); then
    echo "==> ERROR: $missing required entries missing from tarball" >&2
    exit 1
fi

printf '%s\n' "$OUTPUT"
