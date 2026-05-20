# cpp26-adapter — Implementation Plan

**Status:** binding plan v1.0 — locks scope and approach for build phases 0–9.
**Owner:** Paris Moschovakos (parasxos)
**Target completion:** ~25 focused days (≈2–3 months calendar time around CERN work)
**Last updated:** 2026-05-20

---

## 0. Charter

### Mission

Build a Claude Code plugin that turns a general-purpose LLM into a C++26 specialist by stacking four primitives (skill + MCP + agent + hooks) on top of the base model. The plugin biases generation toward C++26 final-form constructs as documented in **ISO/IEC 14882:2026**, independent of current compiler maturity.

### Core policy (the architectural invariant)

1. **Recommendations follow the standard, not the toolchain.**
2. If `clang 22` / `gcc 16` don't yet implement a feature in C++26 final form, suggest it anyway.
3. Compiler errors flow through to the user as **information** (classified `compiler-lag` vs `bug`), never as automatic fixes.
4. Stay **compiler-agnostic** in the suggestion layer (Layers A/B). Compiler-aware **only** in the verification layer (Layer C, informational pass).
5. Different compilers will diverge slightly; the standard is the source of truth.

### Non-goals

- Rewriting legacy C++23 code unprompted. Only generate fresh code in C++26, or rewrite on explicit request.
- Tracking C++29 drafts. Scope is final-published C++26 only.
- Shipping a compiler. We can reference Bloomberg's `clang-p2996` for reflection compile-checks where useful, but installation is the user's responsibility.
- Building a general-purpose C++ linter. The reviewer agent's job is C++26-specific patterns, not generic style.

### Definition of done (v1.0)

- ≥150 C++26 features structured into a queryable corpus (~30 deep, ~80 shallow, ~40 stub)
- Skill biases LLM toward C++26 idioms automatically; eval suite scores ≥85% correct idiom selection
- MCP exposes 6 lookup tools, backed by corpus + sentence-transformer index
- Reviewer agent classifies output as `pass | needs-changes | compiler-lag-only`
- Installable via `/plugin install` from at least one marketplace (private or public, TBD)
- Quarterly maintenance plan documented and triggered (cron or manual)

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Layer D — BUILD INTEGRATION                                 │
│   /cpp26-init   PostToolUse hook   SessionStart probe        │
├──────────────────────────────────────────────────────────────┤
│  Layer C — VERIFICATION (two-pass, runs as subagent)         │
│   Pass 1: STANDARD compliance (KB-driven, always runs)       │
│   Pass 2: COMPILER compile-check (informational only)        │
│           → classifies failures as bug | compiler-lag        │
├──────────────────────────────────────────────────────────────┤
│  Layer B — IDIOM BIAS (skill, COMPILER-AGNOSTIC)             │
│   Constitution + decision tree + paper IDs                   │
├──────────────────────────────────────────────────────────────┤
│  Layer A — REFERENCE (MCP server)                            │
│   Backed by corpus/ — papers, features, status               │
└──────────────────────────────────────────────────────────────┘
                            ▲
                            │
                     Base LLM (Claude)
```

### Layer roles

| Layer | Primitive | Role | Compiler-aware? |
|---|---|---|---|
| A | MCP server | Authoritative reference lookup | No |
| B | Skill (SKILL.md) | Idiom selection bias | **No** (per policy) |
| C | Subagent | Verification pass | Yes (informational only) |
| D | Hooks + slash command | Build/IDE integration | Yes |

### Information flow for a single interaction

1. User asks Claude: *"Add a serializer for this struct using reflection."*
2. **Layer B** is in context → biases Claude toward `std::meta`, blocks fallback to template trickery.
3. Claude calls **Layer A**: `lookup_feature("static reflection serialize example")` → gets canonical P2996 syntax.
4. Claude generates the code.
5. Claude invokes **Layer C** subagent on the file:
   - Pass 1 (KB): no anti-patterns found, idiom matches paper.
   - Pass 2 (compiler): clangd reports errors → check `status.yaml` → P2996 marked "partial in clang 22" → classify as `compiler-lag`.
6. Final response: code + note "this is correct per C++26 P2996; clang 22 has partial support, full support expected in clang 25 — install `bloomberg/clang-p2996` to compile today."

---

## 2. The Corpus (the long-pole)

### 2.1 Sourcing strategy

| Source | Role |
|---|---|
| **`github.com/cplusplus/papers`** (issue tracker) | Master index — filter by milestone "C++26", status "adopted" |
| **`wg21.link/N5008`** (or the final ratified WD number) | Ground-truth working draft |
| **`github.com/cplusplus/draft`** (LaTeX standard source) | Exact wording authority |
| **`cppreference.com/w/cpp/26`** | Human-readable feature index (community-maintained, CC-BY-SA) |
| **WG21 trip reports** (Sutter, Stroustrup, isocpp.org) | Editorial context |
| **Individual papers** (`wg21.link/PXXXXRN`) | Per-feature canonical text |

### 2.2 Filter algorithm

```
1. Pull all GitHub issues in cplusplus/papers
2. Filter: milestone == "C++26" AND status label contains "adopted"
3. For each, identify the "adopted revision" (highest R-number voted in)
4. Remove papers later withdrawn or superseded
5. Cross-check against cppreference C++26 page
6. Output: papers.csv (~150 rows)
```

### 2.3 Tiering

Not all 150 papers deserve equal depth. Three tiers:

| Tier | Count | Depth | Source effort |
|---|---|---|---|
| **Major** (transformative for style) | ~30 | Full schema: problem, motivation, all canonical examples, pre-C++26 equivalent, gotchas, compiler-status row | Hand-curated + LLM-assisted |
| **Minor** (small additions, new functions) | ~80 | Title + 1-paragraph summary + one example + pre/post comparison if obvious | Auto-extracted, spot-checked 10% |
| **Editorial** (footnotes, defect fixes) | ~40 | Title + abstract only | Auto-extracted, no review |

### 2.4 Major-tier seed list (refine in Phase 1a)

Papers expected to qualify as major (subject to final verification):

| Paper | Title | Category |
|---|---|---|
| P2996 | Reflection for C++26 | core |
| P3068 / P3096 / P3394 / P3491 | Reflection supporting machinery | core |
| P2900 | Contracts (preconditions, postconditions, contract_assert) | core |
| P2300 | std::execution (sender/receiver async) | library |
| P1306 | Expansion statements (`template for`) | core |
| P2662 | Pack indexing (`pack...[N]`) | core |
| P2573 | `= delete("reason")` | core |
| P2893 | Variadic friends | core |
| P1967 | `#embed` | preprocessor |
| P2795 | Erroneous behavior / `[[indeterminate]]` | core |
| P1673 | `std::linalg` (BLAS-style linear algebra) | library |
| P1121 / P2545 | Hazard pointers / RCU | library |
| P3471 | Library hardening profile | library |
| P3068 | Constexpr exception types | core |
| P1938 | `if consteval` polish | core |
| P2169 | Placeholder with no name | core |
| P0843 | `std::inplace_vector` | library |

(Final list locked after Phase 1a discovery.)

### 2.5 Feature record schema

Definitive schema for `corpus/features/PXXXX.yaml`:

```yaml
id: P2996                              # WG21 paper number
title: "Reflection for C++26"
revision_adopted: R13                  # the revision voted into the standard
adopted_at: "Sofia 2025-06"            # meeting where adopted
category: core                         # core | library | preprocessor | editorial
tier: major                            # major | minor | editorial
canonical_url: https://wg21.link/P2996R13
cppreference_url: https://en.cppreference.com/w/cpp/experimental/reflect

problem: |
  Multi-paragraph statement of the problem the feature solves. What is hard or
  impossible in pre-C++26 C++? What workarounds did people use? Why were those
  workarounds insufficient?

motivation: |
  Why this design? Why now? What did the committee weigh? What was rejected?
  Drawn from the paper's "Motivation" or "Design Discussion" sections.

key_syntax_elements:
  - "^^ (reflection operator) — produces std::meta::info"
  - "[: ... :] (splicer) — re-injects reflected entity"
  - "std::meta::* (introspection API namespace)"

canonical_examples:
  - title: "Enum to string"
    code: |
      // Full compilable snippet under -std=c++2c
      template <typename E> requires std::is_enum_v<E>
      constexpr std::string_view enum_name(E v) {
        template for (constexpr auto e : std::meta::enumerators_of(^^E))
          if ([:e:] == v) return std::meta::identifier_of(e);
        return "<unknown>";
      }
    explanation: |
      What this replaces, why it's better, anything subtle.

pre_cpp26_equivalent: |
  - X-macros — define enum + string list in tandem macro pair
  - Boost.Describe — requires BOOST_DESCRIBE_STRUCT per type
  - magic_enum — limited to enums in compile-time-known integral ranges
  - External codegen — build-step complexity

gotchas:
  - Reflection happens in constant evaluation only.
  - Splicers must appear in specific syntactic contexts.
  - std::meta::info is not directly printable — use identifier_of().
  - Some queries are O(n) over members; careful in large types.

compiler_status:
  # Captured in corpus/status.yaml, repeated here for record completeness.
  # NOT consulted by Layer A/B; only Layer C Pass 2.
  clang-22:
    support: partial
    flag: "-std=c++2c"
    notes: "Core only, no std::meta::reflect_*"
  clang-p2996:
    support: full
    flag: "-std=c++2c -freflection-latest"
    notes: "Bloomberg experimental fork"
  gcc-16:
    support: none
    notes: "Tracking; no release date"
  msvc-19.40:
    support: none

related_papers: [P3068, P3096, P3394, P3491, P1306]

keywords: [reflect, std::meta, splice, "^^", "template for"]
```

---

## 3. Phase plan

Effort assumes one focused person. Calendar estimate uses 1 FTE.

### Phase 0 — Setup & decisions (½ day)

| Sub-task | Deliverable |
|---|---|
| Lock scope (already done: full plan, all 4 layers) | This PLAN.md |
| Lock distribution (TBD — recommend public-but-low-key) | README license section |
| Pick KB storage: YAML files in git + SQLite built at install | (already chosen here) |
| Repo skeleton (already created) | `~/code/parasxos/plugins/cpp26-adapter/` |
| Choose corpus license: code MIT, corpus CC-BY-SA 4.0 | `LICENSE-CODE`, `LICENSE-CORPUS` |
| First commit | Initial git history |

**Acceptance:** repo cloneable, PLAN.md committed, skeleton in place.

---

### Phase 1 — Corpus assembly (5–8 days) — *the real work*

#### 1a. Master index (1 day)

- [ ] Script `corpus/scripts/fetch_index.py`:
  - Hit GitHub API for `cplusplus/papers` issues
  - Filter milestone="C++26", state="closed", label contains "adopted"
  - For each: extract paper_id, title, adopted_revision (from issue body), adoption_meeting
- [ ] Cross-check against cppreference C++26 page (manual diff)
- [ ] Cross-check against final WG21 plenary trip report
- [ ] Manual: assign tier (major/minor/editorial) per row
- [ ] Output: `corpus/papers.csv`

**Acceptance:** ≥140 rows, all tiered, spot-check 20 random against cppreference.

#### 1b. Paper fetcher (1 day)

- [ ] Script `corpus/scripts/fetch_papers.py`:
  - For each paper in `papers.csv`, resolve `wg21.link/PXXXX` to latest revision
  - Download HTML / PDF / Bikeshed source as available
  - Cache under `corpus/raw/PXXXXRN.{html,pdf,bs}`
  - Track failures in `corpus/raw/fetch_log.json`
- [ ] Retry/escalate failures manually

**Acceptance:** ≥95% of papers fetched; manual override possible for stragglers.

#### 1c. Content extraction (3–5 days) — *the slog*

**Major tier (~30, hand-curated + LLM-assisted):**

- [ ] For each major paper, work through it personally with LLM help
- [ ] Fill full schema (problem, motivation, examples, pre-26 equivalent, gotchas)
- [ ] Validate every code example: parse-check via `clang -std=c++2c -fsyntax-only` where supported; syntactic inspection where not
- [ ] Output: `corpus/features/PXXXX.yaml`
- [ ] Estimate: 2–3 hours per paper × 30 = 60–90 hours

**Minor tier (~80, auto-extracted):**

- [ ] Script `corpus/scripts/extract_minor.py`:
  - Feed paper text to Claude with a structured prompt
  - Capture title, 1-paragraph summary, first canonical example, pre/post if extractable
- [ ] Spot-check 10% manually; correct as needed
- [ ] Output: `corpus/features/PXXXX.yaml` with `tier: minor`

**Editorial tier (~40, stub):**

- [ ] Script: title + abstract auto-extracted, no review
- [ ] Output: `corpus/features/PXXXX.yaml` with `tier: editorial`

**Acceptance:** every paper in `papers.csv` has a corresponding YAML; major-tier validated against canonical examples.

#### 1d. Compiler status table (½ day)

- [ ] Pull from:
  - `clang.llvm.org/cxx_status.html`
  - `gcc.gnu.org/projects/cxx-status.html`
  - Microsoft Learn docs for MSVC
  - `bloomberg/clang-p2996` README (for P2996-specific)
- [ ] Capture as `corpus/status.yaml`:

```yaml
# corpus/status.yaml
compilers:
  clang-22:
    release: "2026-Q1"
    cxx2c_flag: "-std=c++2c"
  clang-p2996:
    release: "rolling"
    cxx2c_flag: "-std=c++2c -freflection-latest"
  gcc-16:
    release: "2026-Q4"
    cxx2c_flag: "-std=c++2c"
  msvc-19.40:
    release: "2026-Q2"
    cxx2c_flag: "/std:c++latest"

features:
  P2996:
    clang-22: { support: partial, notes: "Core only" }
    clang-p2996: { support: full, notes: "Bloomberg fork" }
    gcc-16: { support: none }
    msvc-19.40: { support: none }
  P2900:
    clang-22: { support: none }
    gcc-16: { support: none }
    # ... etc
```

- [ ] Document refresh schedule (quarterly manual)

**Acceptance:** all major-tier features have a status row for at least clang-22, gcc-16, msvc-latest.

#### 1e. Validation (1 day)

- [ ] Read 10 random feature YAMLs end-to-end
- [ ] CI job: run all canonical examples through latest clang under `-std=c++2c -fsyntax-only` (where compiler supports the feature) — pass/skip/fail per example
- [ ] Fix discovered issues

**Acceptance:** zero parse-failures on examples where compiler claims full support.

---

### Phase 2 — Layer A: Reference MCP server (3 days)

Python FastMCP server in `mcp-server/`.

#### 2a. Server scaffold (½ day)

- [ ] `pyproject.toml` with FastMCP, sentence-transformers, pyyaml, pydantic
- [ ] Entry point `mcp-server/src/cpp26_ref/server.py`
- [ ] Build step: `mcp-server/build.py` converts `corpus/features/*.yaml` → `corpus/cpp26.sqlite`
- [ ] Vector index over (title + problem + keywords) using `all-MiniLM-L6-v2`

#### 2b. Tool implementations (1.5 days)

```python
@mcp.tool
def lookup_paper(paper_id: str) -> dict:
    """Return the full feature record for a WG21 paper ID (e.g., 'P2996')."""

@mcp.tool
def lookup_feature(query: str, top_k: int = 3) -> list[dict]:
    """Natural-language search across features. Returns top-k matches."""

@mcp.tool
def compare_idioms(task: str) -> dict:
    """Given a task description, return the C++26 idiom paired with its
    pre-C++26 equivalent. e.g., 'enum to string' → reflection vs X-macros."""

@mcp.tool
def list_features(category: str = None, tier: str = None) -> list[dict]:
    """Filtered listing — useful for browsing 'all major core features'."""

@mcp.tool
def feature_status(paper_id: str, compiler: str = None) -> dict:
    """Compiler implementation status for a feature. Informational only —
    do NOT use to gate suggestions."""

@mcp.tool
def canonical_example(paper_id: str, example_id: int = 0) -> dict:
    """Return a specific canonical example with full code + explanation."""
```

#### 2c. Tests (1 day)

- [ ] Unit test per tool against a fixture corpus of 5 features
- [ ] Integration test: spin up server, exercise full lookup flow via stdio
- [ ] Latency target: <100ms for lookups, <500ms for vector search

**Acceptance:** all 6 tools work; tests green; server starts in <2 seconds.

---

### Phase 3 — Layer B: Idiom skill (1–2 days, iterate later)

`skills/cpp26-idioms/SKILL.md`. Outline:

```markdown
---
name: cpp26-idioms
description: When generating C++ code, target the C++26 standard (-std=c++2c)
  and prefer C++26 idioms over older equivalents, independent of current
  compiler support.
---

# C++26 Idiom Bias

## Constitution

Generate against the **C++26 standard**, not the current compiler. If a feature
is in C++26 final form, suggest it. The compiler will catch up; user code won't
have to be rewritten when it does.

When uncertain about syntax, call MCP:
  - cpp26-ref.lookup_paper(<id>)
  - cpp26-ref.lookup_feature(<query>)
  - cpp26-ref.compare_idioms(<task>)
  - cpp26-ref.canonical_example(<id>)

## Standard target
Default to `-std=c++2c` in CMakeLists.txt / build flags.

## Decision rules (prefer LEFT column unconditionally)

| Use C++26 …                       | …over pre-C++26 …               | Paper |
|-----------------------------------|----------------------------------|-------|
| std::meta::reflect_of + splice    | X-macros / Boost.Describe        | P2996 |
| template for expansion stmt       | recursive variadic templates     | P1306 |
| contract_assert                   | assert()                         | P2900 |
| [[pre:]] / [[post:]]              | manual preconditions in body     | P2900 |
| std::execution::sender            | std::async / raw futures         | P2300 |
| pack indexing pack...[N]          | std::tuple_element_t<N, …>       | P2662 |
| = delete("reason")                | deleted with adjacent comment    | P2573 |
| variadic friends                  | macro repetition                 | P2893 |
| #embed                            | xxd / cmake configure_file       | P1967 |
| [[indeterminate]]                 | UB tricks for sentinels          | P2795 |
| std::linalg                       | hand-rolled BLAS wrappers        | P1673 |
| hazard pointers / RCU             | shared_ptr ref-cycle ad-hoc      | P1121 |
| library hardening profile         | manual bounds checks             | P3471 |
| constexpr exceptions              | error_code at constant eval      | P3068 |
| std::inplace_vector               | static array + length tracking   | P0843 |
| placeholder _ (no-name binding)   | _<n> dummy or [[maybe_unused]]   | P2169 |

(~15+ rules; final table reflects major-tier corpus.)

## When to ignore this skill
- Project's CMakeLists/build files explicitly target an older standard
  AND the user has not asked for modernization.
- Embedded target with documented toolchain constraints (ARM bare-metal,
  FreeRTOS markers).
- Test code touching a legacy module — keep consistent with surroundings.

## Anti-patterns to flag (if encountered while modifying code)
- Hand-written enum-to-string switch → suggest reflection
- BOOST_DESCRIBE_STRUCT → suggest reflection
- assert() in new code → suggest contract_assert
- std::async for fan-out → suggest std::execution

## On compiler errors involving C++26 features
Inform the user: "This is correct per C++26 (see <paper>). Current
<compiler> doesn't yet implement it. Options: (1) wait for compiler
update, (2) install Bloomberg's clang-p2996 fork (for reflection),
(3) keep the C++26 form behind a feature-test macro for now."

Do NOT downgrade the suggestion to a pre-C++26 idiom on the user's behalf.
```

**Acceptance:** SKILL.md ≤300 lines; decision-tree table covers all major-tier idioms.

---

### Phase 4 — Layer C: Reviewer subagent (4–5 days)

`agents/cpp26-reviewer.md` — a Claude Code subagent with explicit two-pass logic.

#### 4a. Agent spec (1 day)

YAML frontmatter:
```yaml
name: cpp26-reviewer
description: Review a C++ file or diff for C++26 standard compliance.
  Runs two passes: standard-compliance (always) and compiler-check (informational).
  Returns structured pass/fail with classification.
tools: [Read, Bash, Grep, mcp__cpp26-ref__*]
model: sonnet
```

#### 4b. Pass 1 — standard compliance (1.5 days)

Detect "C++23 fallback" patterns. Two-stage detection:

**Stage 1 — regex (v0.1):**
```python
PATTERNS = [
    (r'\bassert\s*\(', "use contract_assert instead", "P2900"),
    (r'\bBOOST_DESCRIBE_', "use reflection instead", "P2996"),
    (r'\bstd::async\s*\(', "use std::execution sender instead", "P2300"),
    (r'#define\s+\w+\s*\([^)]*\).+\\$', "consider reflection/template for", "P2996/P1306"),
    # ... ~20 patterns
]
```

**Stage 2 — clang-tidy custom checks (v0.2, later):**
- AST-based detection (more accurate, slower to write)
- Migrate from regex incrementally

#### 4c. Pass 2 — compiler check (1.5 days)

- Invoke `clangd` via LSP (or `clang -fsyntax-only` for simpler integration)
- Parse diagnostics
- For each diagnostic, cross-reference `corpus/status.yaml`:
  - If feature mentioned in error is "not supported by this compiler" → classify `compiler-lag`
  - Otherwise → classify `bug`

Conservative bias: only classify as `compiler-lag` when `status.yaml` explicitly says "not supported." Default → `bug`.

#### 4d. Output schema

```yaml
status: pass | needs-changes | compiler-lag-only
standard_compliance:
  pass: true
  antipatterns: []          # list of (line, pattern, suggestion, paper_ref)
compile_check:
  pass: false
  bugs: []                  # genuine errors
  compiler_lag: []          # errors caused by missing compiler support
    # each entry: { line, feature, paper, "expected in <compiler> <version>" }
```

#### 4e. Tests (1 day)

- [ ] Fixture: 10 C++ snippets (5 clean C++26, 5 with deliberate anti-patterns)
- [ ] Each snippet has expected classification
- [ ] CI runs the agent against the fixture; assert classifications match

**Acceptance:** ≥90% classification accuracy on fixture; zero false-negatives on bugs.

---

### Phase 5 — Layer D: Build integration (1–2 days)

#### 5a. `/cpp26-init` slash command (½ day)

`commands/cpp26-init.md`. When invoked:
- Emit `CMakeLists.txt` (or patch existing) with:
  - `set(CMAKE_CXX_STANDARD 26)`
  - `add_compile_options(-std=c++2c)`
  - `set(CMAKE_EXPORT_COMPILE_COMMANDS ON)`
- Emit `.clangd` with toolchain pointer
- Emit `.cpp26-adapter.yaml` (project-local overrides)
- Update README with toolchain expectations

#### 5b. Hooks (`hooks/hooks.json`) (½ day)

```json
{
  "hooks": {
    "SessionStart": [{
      "command": "tools/check_toolchain.sh",
      "description": "Verify clang ≥22; warn if older"
    }],
    "PostToolUse": [{
      "matcher": "Edit",
      "filePattern": "*.{cpp,h,hpp,cxx,cc}",
      "command": "tools/quick_lint.sh",
      "description": "Fast regex-based Pass-1 check"
    }]
  }
}
```

#### 5c. Toolchain probe + lint scripts (½ day)

- [ ] `tools/check_toolchain.sh` — detects clang version, reports
- [ ] `tools/quick_lint.sh` — regex-based subset of Pass 1, fast

**Acceptance:** `/cpp26-init` produces a buildable CMake project; hooks fire on edits.

---

### Phase 6 — Plugin packaging (½ day)

- [ ] Write `.claude-plugin/plugin.json`:
```json
{
  "name": "cpp26-adapter",
  "version": "1.0.0",
  "description": "Turn Claude into a C++26 specialist via standard-first idiom bias, reference MCP, and verification.",
  "author": { "name": "Paris Moschovakos" }
}
```
- [ ] Wire `.mcp.json` to spawn the local MCP server
- [ ] Document install in README
- [ ] Test `/plugin install` on a clean Claude Code instance

**Acceptance:** clean install on a second machine; full feature path works end-to-end.

---

### Phase 7 — Eval & iteration (3–4 days)

This is where most plugins stall (ship, no iteration). Plan for it explicitly.

#### 7a. Eval suite (1 day)

30 representative C++ tasks. Each covers a major-tier rule from the skill:

| # | Task | Tests rule |
|---|---|---|
| 1 | "Write enum-to-string for `enum class Color { Red, Green, Blue };`" | reflection (P2996) |
| 2 | "Add precondition `n > 0` to this function" | contracts (P2900) |
| 3 | "Make this function fan-out async" | senders/receivers (P2300) |
| 4 | "Serialize this struct to JSON" | reflection (P2996) |
| 5 | "Implement compile-time loop over members" | template for (P1306) |
| 6 | "Embed a binary file as compile-time data" | #embed (P1967) |
| 7 | "Type-safe variadic visitor" | pack indexing (P2662) |
| 8 | "Delete this constructor with reason" | = delete("reason") (P2573) |
| ... | ... | ... |

#### 7b. Run eval, plugin OFF vs ON (½ day)

- [ ] Run all 30 tasks twice (with/without plugin)
- [ ] Score outputs on 3 axes:
  - **Standard compliance:** uses C++26 idiom or fallback? (binary)
  - **Syntactic correctness:** parses under clang `-std=c++2c`? (binary)
  - **Idiomatic quality:** LLM-judged 1–5
- [ ] Record in `eval/results-v0.1.md`

#### 7c. Iterate (2–3 days)

- [ ] Identify systematic failures (e.g., LLM keeps using `assert` despite skill)
- [ ] Strengthen skill prose for those cases
- [ ] If still failing → hook-enforced injection (PostToolUse hook auto-amends generated code)
- [ ] Re-run eval until ≥85% standard-compliance

**Acceptance v0.1:** 70% correct idiom selection. **Acceptance v1.0:** 90%.

---

### Phase 8 — Distribution (1 day)

Decision (locked from earlier): **publish.** Three sub-options to choose between:

| Option | Effort | Reach |
|---|---|---|
| Personal marketplace (your GitHub repo as a marketplace) | ½ day | Anyone you tell |
| Submit to `wshobson/agents` (claude-code-workflows) | 1 day + review wait | Curated audience |
| Submit to `anthropics/claude-plugins-official` | 1 day + review wait | Maximum discoverability |

Recommend: personal marketplace first (`parasxos/claude-plugins`), then submit to one or both upstream marketplaces once v1.0 is stable.

Companion artifacts:
- [ ] Blog post on the architecture (post to `/r/cpp`, isocpp.org, Hacker News)
- [ ] Demo video (5 min): show "before" vs "after" on 3 representative tasks
- [ ] Public eval results

**Acceptance:** plugin discoverable via at least one marketplace; ≥1 external user before declaring success.

---

### Phase 9 — Maintenance (ongoing, ~1 day/quarter)

- [ ] Monthly cron: diff `cplusplus/papers` for new "C++26" issues (defect reports, corrigenda)
- [ ] Quarterly: refresh `corpus/status.yaml` from compiler release notes
- [ ] Re-run eval suite quarterly; track regressions
- [ ] Triage incoming GitHub issues (if public)
- [ ] Add new idiom patterns as they emerge in real use

---

## 4. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Paper extraction harder than scoped | High | Medium | Tier system; hand-curate top 30 only; auto-extract rest |
| 2 | LLM ignores the skill despite prose | Medium | High | Eval suite + iteration; hook-enforced injection as fallback |
| 3 | Compiler status data goes stale | Certain | Low | Quarterly refresh documented; staleness surfaced in MCP responses |
| 4 | Bloomberg clang-p2996 diverges from P2996 | Medium | Medium | Track revision in corpus; refresh on new R |
| 5 | Reviewer false-positives on real bugs (`compiler-lag` classification) | Medium | High | Conservative default: only classify lag when `status.yaml` says so |
| 6 | Skill over-applies to legacy projects | Medium | Low | "When to ignore" section + project detection |
| 7 | Maintainer burnout | Medium | High | Distribution strategy determines surface area; recruit help via issues |
| 8 | C++26 amended post-publication | Low | Medium | Use `cplusplus/draft` HEAD as truth; refresh periodically |
| 9 | MCP latency too high (lookups feel slow) | Low | Medium | SQLite + in-memory vector index; target <100ms |
| 10 | Eval over-fits to test tasks | Medium | Medium | Diverse task set; rotate examples between releases |

---

## 5. Total effort

| Phase | Effort | Calendar (1 FTE) |
|---|---|---|
| 0. Setup | ½ day | day 1 |
| 1. Corpus | 5–8 days | weeks 1–2 |
| 2. MCP | 3 days | week 2 |
| 3. Skill | 1–2 days | week 2 (parallel) |
| 4. Reviewer | 4–5 days | week 3 |
| 5. Build integration | 1–2 days | week 3 |
| 6. Packaging | ½ day | week 4 |
| 7. Eval & iterate | 3–4 days | week 4 |
| 8. Distribution | 1 day | week 4 |
| **Total** | **~20–25 days** | **4 weeks focused** |

Realistic calendar around CERN work: **2–3 months.**

---

## 6. Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-20 | Project home: `~/code/parasxos/plugins/cpp26-adapter/` | New repo under personal GitHub namespace, room for future plugins |
| 2026-05-20 | Scope: full plan, all 4 layers, ~150 features | Maximum ambition; tiered depth keeps it tractable |
| 2026-05-20 | Storage: YAML in git + SQLite at install | YAML readable in PRs, SQLite fast at query time |
| 2026-05-20 | Compiler-aware in Layer C only | Per user's standard-first policy invariant |
| 2026-05-20 | License: MIT code, CC-BY-SA 4.0 corpus | Corpus derives partly from cppreference (CC-BY-SA); compatible |

---

## 7. Open questions

These don't block Phase 0–1 but should be resolved before Phase 4 or 7:

1. **Bloomberg clang-p2996 — bundle or just reference?** Recommend reference; users install themselves.
2. **Should reviewer agent block PR merges or just warn?** v1.0 = warn only; v2.0 may add merge-blocking via CI integration.
3. **Library scope final cut.** Confirm `std::linalg` and `std::execution` are major-tier worth full curation, or shallow-tier.
4. **Distribution timing.** Personal marketplace at v0.1 or only at v1.0?

---

## 8. Glossary

- **Final form** — the version of a paper voted into ISO/IEC 14882:2026.
- **Standard-first policy** — recommendations follow the standard, never the compiler.
- **Compiler-lag** — a compile failure caused by the compiler not yet implementing a C++26 feature; classified as informational, not a bug.
- **Tier** — corpus depth tier (major/minor/editorial).
- **MCP** — Model Context Protocol; how Claude Code talks to the reference server.
- **LSP** — Language Server Protocol; how Claude Code talks to clangd.
- **WG21** — ISO C++ standards committee.
- **Paper ID** — WG21 reference like `P2996`. Latest revision suffixed: `P2996R13`.

---

*End of binding plan. Implementation begins Phase 0.*
