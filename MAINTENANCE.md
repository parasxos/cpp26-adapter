# Maintenance — cpp26-adapter

Quarterly cadence. Each refresh is ~1 day of focused work for the
solo maintainer.

## When to refresh

- **Calendar**: every 3 months (Jan / Apr / Jul / Oct). The C++ working
  group meets ~5 times per year; a quarterly cycle catches each meeting
  within 1-2 months of adoption.
- **On demand**: a new WG21 meeting concluded → run early.
- **On compiler release**: clang / gcc / msvc has a new major →
  refresh `status.yaml`.

## One-command refresh

```bash
tools/refresh.sh                 # the corpus refresh (no eval)
tools/refresh.sh --with-eval     # add the 39-task eval suite
```

What it does (and what's manual afterwards):

1. **`fetch_index.py`** — re-pulls the C++26 paper list from
   `cplusplus/papers`. Overwrites `corpus/index.yaml`.
   *Manual after:* re-tier any new rows (heuristic gives stub by
   default); decide whether any newly-adopted paper deserves the
   deep tier.
2. **`refresh_status.py`** — scrapes upstream cxx-status pages and
   prints what's mentioned per deep-tier paper. Does **not** write to
   `status.yaml`.
   *Manual after:* hand-merge the relevant lines into `status.yaml`;
   bump `last_refreshed`.
3. **`validate_corpus.py`** — schema check, cross-ref check, deep-tier
   syntax check.
   *Manual after:* fix any schema or orphan issues. Syntax FAILs are
   informational below the C++26 compiler baseline.
4. **(optional) `eval/run.py`** — 39-task suite, ~$15-25 in API calls.
   *Manual after:* if axis-1 dropped, follow the Phase-7c iteration
   playbook in `eval/README.md` until ≥85%.

## Promoting a paper to deep tier

When a new C++26 paper warrants a hand-curated reference (e.g., a
late-DR feature that landed in the IS):

1. Add the paper id to `DEEP_TIER` in `corpus/scripts/fetch_index.py`.
2. Re-run `fetch_index.py` so the tier is reflected in `index.yaml`.
3. Author `corpus/references/<id>.md` following the structure of any
   of the 16 existing deep refs (frontmatter + Problem + Key syntax +
   Canonical example + Pre-C++26 equivalent + Gotchas + Related).
4. Add the paper to `corpus/status.yaml` with at-least clang-22 /
   clang-p2996 / gcc-16 / msvc-19.40 entries.
5. Add 1+ row to the SKILL.md decision table referencing the new ref.
6. Add 1+ task to `eval/tasks.yaml` testing the canonical idiom.
7. Re-run validator + eval; commit.

## Files this project owns

```
corpus/
  index.yaml          ← rewritten by fetch_index.py; tier edits manual
  status.yaml         ← edited by hand, informed by refresh_status.py
  references/         ← deep refs hand-authored; shallow/stub by gen_refs.py
  scripts/            ← three maintenance scripts
  raw/                ← gitignored; raw paper HTML/PDF cache

skills/cpp26-idioms/
  SKILL.md            ← the constitution + decision table; edit per failing eval
  references/         ← symlink to corpus/references in dev; copy in release tarball

agents/cpp26-reviewer.md
                      ← two-pass review subagent

tools/
  cpp26_lint/patterns.yaml  ← regex anti-pattern table; extend per failing eval
  cpp26_lint/quick_lint.py  ← runner
  check_toolchain.sh        ← SessionStart probe
  validate_corpus.py        ← Phase-1e validator
  package.sh                ← release tarball builder
  refresh.sh                ← this file's entry point

eval/
  tasks.yaml          ← held suite; rotate 25% between minor releases
  run.py              ← harness
  README.md           ← usage + Phase-7c playbook

mcp-server/
  src/cpp26_ref/server.py   ← 3-tool MCP; rarely needs edits
  pyproject.toml            ← deps: mcp, pyyaml, pydantic, rapidfuzz
  tests/                    ← pytest; run via `pytest mcp-server/tests`

PLAN.md               ← the binding plan (v1.1); reference, not edited per refresh
README.md             ← user-facing layout overview
MAINTENANCE.md        ← this file
```

## Plugin naming convention

For any future plugin landing on `parasxos/claude-plugins`:

- Form: `<domain>-<verb-or-noun>` (e.g. `cpp26-adapter`, `cern-dcs-toolkit`, `comms-orchestrator`).
- No `paris-` / `parasxos-` / `claude-` prefix — the marketplace URL already namespaces.
- All lowercase, hyphen-separated.

## Version bumps

SemVer 2.0:
- **Patch (0.9.x → 0.9.x+1)**: corpus refresh, status updates, one-off
  reference edits, eval task swaps.
- **Minor (0.9.x → 0.10.0)**: new feature in the plugin's own surface
  (skill restructuring, new MCP tool, new subagent).
- **Major (1.x → 2.0)**: breaking change to the MCP tool signatures, the
  subagent's output schema, or the standard-first invariant. v1.0 was cut
  on 2026-05-26 once the eval gate held across two successive refreshes
  (v0.9.0 95%, v0.9.1 90%).

After each refresh, bump the version in `.claude-plugin/plugin.json`
and tag locally; push the tag at the next distribution event.

## Trigger conditions

These signals mean "refresh now, don't wait for the quarter":

- A WG21 meeting concluded (Sofia, Issaquah, Kona, …).
- A new clang or gcc major shipped.
- A user-reported eval failure suggests the corpus / skill / lint
  is out of step.
- The Bloomberg clang-p2996 fork bumps its tracked revision.
