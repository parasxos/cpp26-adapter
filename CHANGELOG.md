# Changelog

All notable changes to `cpp26-adapter` are documented here.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
SemVer follows the policy in [`MAINTENANCE.md`](MAINTENANCE.md): patch
for corpus/status refreshes, minor for plugin-surface changes, major
on two successive eval-passing refreshes.

## [Unreleased]

- Discoverability: GitHub repo topics added (claude-code,
  claude-code-plugin, cpp26, mcp-server, wg21, …).
- Issue templates under `.github/ISSUE_TEMPLATE/` for install
  confirmations, eval task suggestions, and bug reports.
- Announcement bundle at `docs/announce/RELEASE_PREP.md` covering HN,
  r/cpp, r/ClaudeAI, Mastodon/Bluesky/X, and LinkedIn channels.

## [0.9.0] — 2026-05-20

First public release. Feature-complete; eval gate cleared at 95%;
pre-1.0 pending a second successive refresh and ≥1 external installer
per `PLAN.md` §8 acceptance.

### Added

- **Skill `cpp26-idioms`** — 136-line SKILL.md with a 5-rule
  constitution, 20-row decision table mapping pre-C++26 anti-patterns
  to C++26 successors, and a 12-entry anti-pattern regex list.
- **MCP server `cpp26-ref`** — 3 stdio tools (`lookup_paper`,
  `search`, `compiler_status`), in-memory load over `corpus/index.yaml`
  + `corpus/status.yaml`, no SQLite, no embeddings, 352 ms cold
  start, 17 unit + integration tests passing.
- **Subagent `@cpp26-reviewer`** — two-pass review: regex
  anti-pattern Pass 1, `clang -std=c++2c -fsyntax-only` Pass 2 with
  bug-vs-compiler-lag classification routed through
  `mcp__cpp26-ref__compiler_status`. Conservative default — unknown
  classifies as bug.
- **Hooks** — `SessionStart` toolchain probe (informational warn if
  clang < 22 / gcc < 16); `PostToolUse` Pass-1 lint on every C++
  file edit.
- **Slash command `/cpp26-init`** — scaffolds a C++26-ready
  `CMakeLists.txt` (CXX_STANDARD 26, -std=c++2c,
  CMAKE_EXPORT_COMPILE_COMMANDS), `.clangd`, and `.cpp26-adapter.yaml`.
- **Knowledge corpus** — 216 plenary-approved C++26 papers indexed
  from `cplusplus/papers` (cross-checked vs cppreference C++26 page:
  19/20 random match). 16 hand-curated deep references covering
  reflection (P2996), contracts (P2900), `std::execution` (P2300),
  expansion statements (P1306), pack indexing (P2662),
  `= delete("reason")` (P2573), variadic friends (P2893), `#embed`
  (P1967), erroneous behaviour (P2795), `std::linalg` (P1673),
  hazard pointers (P2530), RCU (P2545), library hardening (P3471),
  throw in constant eval (P3068), placeholder `_` (P2169), and
  `std::inplace_vector` (P0843). 52 templated shallow refs and 148
  stubs for full surface coverage.
- **Compiler status matrix** — `corpus/status.yaml` for the 16 deep
  papers across clang-22, clang-p2996, gcc-16, msvc-19.40.
- **Maintenance scaffold** — `tools/refresh.sh`,
  `tools/validate_corpus.py`, `tools/package.sh`,
  `corpus/scripts/{fetch_index,fetch_papers,refresh_status,gen_refs}.py`.
- **Eval harness** — 39-task held suite at `eval/tasks.yaml`;
  3-axis scorer at `eval/run.py` (standard-compliance,
  syntactic correctness, idiomatic-quality LLM-judge); subscription
  auth by default (`CPP26_EVAL_USE_API=1` to opt back into API
  billing).
- **Distribution** — pushed to
  [`parasxos/cpp26-adapter`](https://github.com/parasxos/cpp26-adapter)
  with the 16-commit build history. Marketplace catalog at
  [`parasxos/claude-plugins`](https://github.com/parasxos/claude-plugins).
- **Documentation** — README (marketing-grade synthesis of three
  parallel drafts), `docs/architecture.md` (standard-first invariant
  long-form), `PLAN.md` (binding implementation plan with phase-level
  acceptance criteria), `MAINTENANCE.md` (quarterly refresh process
  and SemVer policy).

### Eval

- Held suite: **37/39 = 95% standard-compliance** (bar ≥85%, +10 pp
  margin). See [`eval/results-v0.9.0.md`](eval/results-v0.9.0.md).

### Known limitations

- Two genuine eval misses recorded in `eval/results-v0.9.0.md`:
  `tuple-sum` (model reaches for `std::index_sequence` inside
  `template for`) and `enable-hardening-cmake` (model cites
  `_LIBCPP_HARDENING_MODE` instead of the standard
  `__STDCPP_HARDENING_MODE`). Candidate `SKILL.md` decision-table
  strengthenings for the next refresh.
- Local clang baseline below 22 (e.g., Apple clang) causes the
  validator's Pass 3 to SKIP all deep-tier syntax checks. Run on
  a clang ≥ 22 host (or `bloomberg/clang-p2996` for reflection
  demos) for full validator coverage.
