#!/usr/bin/env bash
# Fire the v1.0.0 release when the external-installer gate closes.
#
# Prerequisites Paris confirms before running this:
#   1. An install-confirmation issue is open at
#      https://github.com/parasxos/cpp26-adapter/issues  (PLAN.md §8 gate).
#   2. The eval is still at ≥85% on the held suite (you can re-run
#      `tools/refresh.sh --with-eval` to re-confirm).
#   3. CI is green on `main`.
#   4. `gh auth status` shows authenticated as parasxos.
#
# What this script does (idempotent within reason — re-running after
# a partial failure should pick up cleanly):
#
#   plugin repo (parasxos/cpp26-adapter):
#     - bump .claude-plugin/plugin.json to 1.0.0
#     - update CHANGELOG.md with the [1.0.0] header (you fill in
#       prose; the script appends the skeleton)
#     - commit, tag v1.0.0, push tag + main
#     - publish GitHub Release v1.0.0 (NOT prerelease)
#     - update docs/MAINTENANCE.md last-refreshed dates if you choose to
#
#   marketplace repo (parasxos/claude-plugins):
#     - bump the cpp26-adapter ref to v1.0.0
#     - bump the version field to 1.0.0
#     - commit + push
#
# DRY RUN by default — pass --execute to actually do it.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MKT_ROOT="${MKT_ROOT:-$ROOT/../../claude-plugins}"

EXECUTE=0
if [[ "${1:-}" == "--execute" ]]; then
    EXECUTE=1
fi

run() {
    printf '  %s\n' "$*"
    if (( EXECUTE == 1 )); then
        eval "$@"
    fi
}

note() { printf '\n==> %s\n' "$*"; }

note "Preflight"

# 1. Are we on a clean main of the plugin repo?
cd "$ROOT"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "  ✗ working tree dirty; commit or stash first" >&2
    exit 1
fi
if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
    echo "  ✗ not on main; checkout main first" >&2
    exit 1
fi
echo "  ✓ plugin tree clean, on main"

# 2. Does the marketplace repo exist locally?
if [[ ! -d "$MKT_ROOT/.git" ]]; then
    echo "  ✗ marketplace repo not at $MKT_ROOT" >&2
    echo "     Set MKT_ROOT=... before running, or:" >&2
    echo "     git clone https://github.com/parasxos/claude-plugins.git $MKT_ROOT" >&2
    exit 1
fi
if [[ -n "$(git -C "$MKT_ROOT" status --porcelain)" ]]; then
    echo "  ✗ marketplace tree dirty at $MKT_ROOT" >&2
    exit 1
fi
echo "  ✓ marketplace tree clean at $MKT_ROOT"

# 3. Is the v1.0.0 tag already present? Bail.
if git tag --list | grep -qx v1.0.0; then
    echo "  ✗ v1.0.0 tag already exists locally; rolling back is destructive" >&2
    echo "     If you really mean to redo, delete locally + on remote first." >&2
    exit 1
fi
echo "  ✓ v1.0.0 tag does not exist yet"

# 4. Confirm latest eval result.
LATEST_RESULTS=$(ls -t eval/results-v*.md 2>/dev/null | head -1)
if [[ -z "$LATEST_RESULTS" ]]; then
    echo "  ! no eval/results-v*.md found; consider re-running before release" >&2
else
    echo "  latest eval file: $LATEST_RESULTS"
    grep -E '^\| 1 — Standard|MET|NOT MET' "$LATEST_RESULTS" || true
fi

if (( EXECUTE == 0 )); then
    note "DRY RUN — no changes made. Re-run with --execute to actually release."
else
    note "EXECUTE — making changes."
fi

# ---- 1. Plugin repo: bump version + commit + tag + push ------------------

note "Plugin repo: bump plugin.json to 1.0.0"
run "python3 -c \"
import json, pathlib
p = pathlib.Path('.claude-plugin/plugin.json')
m = json.loads(p.read_text())
m['version'] = '1.0.0'
p.write_text(json.dumps(m, indent=2) + '\n')
print(f'  wrote {p}')
\""

note "Plugin repo: append [1.0.0] skeleton to CHANGELOG.md"
TODAY=$(date -u +%Y-%m-%d)
run "python3 - <<PY
import pathlib
p = pathlib.Path('CHANGELOG.md')
text = p.read_text()
needle = '## [Unreleased]'
if needle not in text:
    raise SystemExit('CHANGELOG.md missing [Unreleased] anchor')
new_section = '''## [Unreleased]

…

## [1.0.0] — $TODAY

The first stable release. Both v1.0 gates from PLAN.md §8 closed:
- Two successive published refreshes holding ≥85% standard-compliance
  on the held 39-task eval suite (v0.9.0 at 95%, v0.9.1 at 90%).
- ≥1 external installer confirmed via the install_works.md issue
  template (link: TODO fill in issue URL).

### Changed
- .claude-plugin/plugin.json bumped 0.9.1 → 1.0.0.
- Marketplace pin (parasxos/claude-plugins) bumped to v1.0.0.

### Notes
- README badges + GitHub Release transitioned from prerelease to stable.
- Eval bar policy carried forward unchanged: any v1.x.y release must
  hold ≥85% on the held suite; refresh cadence stays quarterly per
  docs/MAINTENANCE.md.
'''
p.write_text(text.replace(needle, new_section, 1))
print('  CHANGELOG.md updated')
PY"

note "Plugin repo: commit + tag v1.0.0 + push"
run "git add .claude-plugin/plugin.json CHANGELOG.md"
run "git commit -m 'v1.0.0 — both v1.0 gates closed'"
run "git tag -a v1.0.0 -m 'v1.0.0 — eval gate held across v0.9.0 (95%) + v0.9.1 (90%); external installer confirmed'"
run "git push origin main"
run "git push origin v1.0.0"

note "Plugin repo: publish GitHub Release v1.0.0 (NOT prerelease)"
RELEASE_NOTES=/tmp/v1.0.0-release-notes.md
cat > "$RELEASE_NOTES" <<'NOTES_EOF'
> **First stable release.** Both v1.0 gates from PLAN.md §8 closed.

## Eval gate

| Refresh | Plugin ON | Bar | Outcome |
|---|---:|---:|---|
| `v0.9.0` | 37/39 (95%) | ≥85% | ✓ |
| `v0.9.1` | 35/39 (90%) | ≥85% | ✓ |

Two consecutive published refreshes both above the bar.

## External installer

Confirmed via the install-confirmation issue template (link: see CHANGELOG entry for v1.0.0).

## Install

```
/plugin marketplace add parasxos/claude-plugins
/plugin install cpp26-adapter@parasxos/claude-plugins
```

## What's in v1.0.0

No new components vs v0.9.1. v1.0 is the SemVer stability signal — the
MCP tool signatures, the subagent output schema, the SKILL.md
decision-table format, and the eval harness contract are all
stable for the v1.x series. Future v1.x bumps may add tasks to
the held suite, refresh the corpus, or add deep references; they
will not break the surfaces above.

License unchanged — MIT (code) + CC-BY-SA-4.0 (corpus).
NOTES_EOF

run "gh release create v1.0.0 --title 'v1.0.0 — first stable release' --notes-file '$RELEASE_NOTES' --latest"

# ---- 2. Marketplace repo: bump pin + push --------------------------------

note "Marketplace repo: bump cpp26-adapter pin to v1.0.0"
run "python3 - <<PY
import json, pathlib
p = pathlib.Path('$MKT_ROOT/.claude-plugin/marketplace.json')
m = json.loads(p.read_text())
plug = next(x for x in m['plugins'] if x['name'] == 'cpp26-adapter')
plug['version'] = '1.0.0'
plug['source']['ref'] = 'v1.0.0'
p.write_text(json.dumps(m, indent=2) + '\n')
print(f'  wrote {p}')
PY"

run "git -C '$MKT_ROOT' add -A"
run "git -C '$MKT_ROOT' -c user.email=parasxos@gmail.com -c user.name='Paris Moschovakos' commit -m 'Bump cpp26-adapter pin to v1.0.0 (stable release)'"
run "git -C '$MKT_ROOT' push origin main"

note "DONE"
if (( EXECUTE == 0 )); then
    echo "  (this was a DRY RUN — re-run with --execute to actually fire)"
else
    echo "  v1.0.0 is live."
    echo "  Plugin:      https://github.com/parasxos/cpp26-adapter/releases/tag/v1.0.0"
    echo "  Marketplace: https://github.com/parasxos/claude-plugins"
fi
