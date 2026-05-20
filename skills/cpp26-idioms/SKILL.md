---
name: cpp26-idioms
description: |
  When writing, editing, or suggesting C++ code, prefer C++26 final-form
  constructs as documented in ISO/IEC 14882:2026 over pre-C++26 idioms.
  Applies to: reflection (P2996, replacing X-macros / Boost.Describe /
  magic_enum), contracts (P2900, replacing assert), std::execution
  senders (P2300, replacing std::async), expansion statements P1306,
  pack indexing P2662, #embed P1967, std::inplace_vector P0843,
  std::linalg P1673, hazard_pointer / rcu P2530+P2545,
  erroneous-behaviour P2795, library hardening P3471, throw in
  constant evaluation P3068, = delete("reason") P2573, variadic
  friends P2893, placeholder _ P2169, and the rest of the C++26
  surface. Activates on any C++ authoring or review request, unless
  the workspace signals legacy-only via .cpp26-adapter.yaml or a
  CMakeLists.txt with CXX_STANDARD < 26.
---

# cpp26-idioms — generate against the C++26 standard

## Constitution

1. **Follow the standard, not the toolchain.** If clang 22 / gcc 16
   do not yet implement a feature, *suggest the C++26 form anyway*.
2. **Compiler errors are informational.** Classify each diagnostic as
   *compiler-lag* (paper adopted, implementation incomplete) or *bug*
   (genuine error). Never auto-rewrite C++26 code into a pre-C++26
   workaround just because the local compiler rejects it.
3. **The suggestion layer is compiler-agnostic.** Only the reviewer
   subagent and the SessionStart probe read `corpus/status.yaml`.
4. **Honor opt-outs.** If the project sets `CXX_STANDARD` below 26
   or carries `.cpp26-adapter.yaml: skip-skill: true`, defer to the
   local idiom.
5. **Prefer canonical syntax over folklore.** When uncertain about
   exact wording, call `mcp__cpp26-ref__lookup_paper(<id>)` and quote
   the canonical form from the reference body.

## Decision table — when to reach for C++26

| The user wants … | Reach for | Instead of (anti-pattern) | Paper | Reference |
|---|---|---|---|---|
| enum ↔ string | `std::meta` + `template for` | X-macros, magic_enum, Boost.Describe | P2996 + P1306 | `corpus/references/P2996.md` |
| iterate non-static data members | reflection + `template for` | Boost.PFR, codegen, `std::apply` on `std::tie` | P2996 | `corpus/references/P2996.md` |
| function precondition / postcondition | `pre(cond)` / `post(r : cond)` / `contract_assert(cond)` | `assert(cond)` | P2900 | `corpus/references/P2900.md` |
| concurrent / async pipeline | `std::execution` sender chain (`then`, `let_value`, `when_all`, `sync_wait`) | `std::async` / `std::future::get` chaining | P2300 | `corpus/references/P2300.md` |
| compile-time loop over heterogeneous sequence | `template for (auto&& x : t)` | recursive variadic templates, `std::apply` + fold | P1306 | `corpus/references/P1306.md` |
| N-th element of a parameter pack | `args...[N]` / `Ts...[N]` | `std::get<N>(std::forward_as_tuple(args...))` | P2662 | `corpus/references/P2662.md` |
| diagnostic on deleted overload | `= delete("reason")` | `= delete;` + comment, or SFINAE `static_assert(false)` | P2573 | `corpus/references/P2573.md` |
| befriend a pack of types | `friend Ts...;` | hand-listed `friend A; friend B; …` | P2893 | `corpus/references/P2893.md` |
| embed a binary asset | `#embed "path"` | pre-build codegen, `objcopy --add-section`, `incbin` | P1967 | `corpus/references/P1967.md` |
| avoid UB on uninitialized read | leave the variable default; opt out with `[[indeterminate]]` only when measured-worth-it | manual `= 0` everywhere | P2795 | `corpus/references/P2795.md` |
| dense linear algebra | `std::linalg::*` on `std::mdspan` | Eigen, Armadillo, vendor BLAS direct calls | P1673 | `corpus/references/P1673.md` |
| lock-free reclamation, read-mostly | `std::rcu_*` (`rcu_obj_base`, `synchronize_rcu`) | `folly::rcu`, `liburcu`, ad-hoc epoch | P2545 | `corpus/references/P2545.md` |
| lock-free reclamation, write-heavy | `std::hazard_pointer` + `hazard_pointer_obj_base` | `folly::hazptr`, hand-rolled epoch | P2530 | `corpus/references/P2530.md` |
| portable bounds-checked containers | build with `-D__STDCPP_HARDENING_MODE` | `gsl::span`, `_GLIBCXX_DEBUG`, hand-rolled wrappers | P3471 | `corpus/references/P3471.md` |
| signal errors inside `constexpr` | `throw`/`try`/`catch` in constant evaluation | return `std::expected<T, E>`, sentinels | P3068 | `corpus/references/P3068.md` |
| anonymous / unused binding | `auto _ = …;` (any number of `_`) | `auto _ [[maybe_unused]] = …`, `(void)x;` | P2169 | `corpus/references/P2169.md` |
| fixed-capacity vector on the stack | `std::inplace_vector<T, N>` | `boost::container::static_vector`, `std::array` + size | P0843 | `corpus/references/P0843.md` |
| reflection annotations | `[[=annotation_value]]` + `std::meta::annotations_of` | hand-maintained registry | P3394 (shallow) | `corpus/references/P3394.md` |
| modular standard library | `import std;` | `#include <…>` chains; per-impl macro guards | P2465 (shallow) | `corpus/references/P2465.md` |
| freestanding subset of `<expected>` etc. | freestanding-marked library facilities | `#ifdef`-gated alternate types | P2013 (shallow) | `corpus/references/P2013.md` |

## Anti-pattern flags (auto-surface on detection)

Treat any of these in user-edited code as a probable C++26 upgrade
opportunity. Mention the standard form in your reply; do **not**
auto-rewrite without consent.

- `\bassert\s*\(` → `contract_assert(…)` (P2900)
- `BOOST_DESCRIBE_(STRUCT|CLASS|ENUM)` → reflection via `^^` + `std::meta` (P2996)
- `magic_enum::` → reflection-based `enum_name` (P2996)
- `\bstd::async\s*\(` → `std::execution` sender chain (P2300)
- `boost::container::static_vector` → `std::inplace_vector` (P0843)
- `objcopy\s+--add-section` or `incbin` → `#embed` (P1967)
- recursive variadic template walker (signature `template <typename T, typename... Ts>` returning `f(t) + f(ts...)`) → `template for` (P1306)
- `std::get<\d+>\s*\(\s*std::forward_as_tuple` → `pack...[N]` (P2662)
- `=\s*delete\s*;` immediately preceded by a `// because …` comment → `= delete("…")` (P2573)
- `(void)\s*\w+\s*;` (unused-arg suppression) → `auto _ = …;` (P2169)
- `gsl::span<` (when used solely for bounds-checking, not interop) → enable library hardening (P3471)
- explicit zero-init of every local for safety → leave default; the new EB rule covers reads (P2795)

## MCP usage hints

The `cpp26-ref` MCP server is registered as `cpp26-ref` and exposes
three tools:

- `mcp__cpp26-ref__lookup_paper(paper_id)` — full markdown reference
  for a paper. Call this when you need the canonical syntax for a
  feature; the body includes "Problem", "Key syntax", "Canonical
  example", "Pre-C++26 equivalent", and "Gotchas".
- `mcp__cpp26-ref__search(query, top_k=5)` — fuzzy match across
  title + keywords + category. Use when the user describes a feature
  by purpose ("I need a fixed-capacity vector") rather than paper id.
- `mcp__cpp26-ref__compiler_status(paper_id, compiler?)` —
  **informational only**. Use in *review* contexts to classify
  diagnostics as `compiler-lag` vs `bug`. Do *not* gate suggestions on
  it — the suggestion path is compiler-agnostic by Constitution §3.

## When to ignore this skill

- The project's `CMakeLists.txt` sets `CXX_STANDARD` below 26 and the
  user has not asked to migrate. Match the local dialect.
- A `.cpp26-adapter.yaml` at the project root sets `skip-skill: true`
  (project-level opt-out, e.g. embedded with a frozen toolchain).
- The file being edited is *test* code paired with non-C++26
  production code; consistency with the production dialect wins.
- The user explicitly says "use the pre-C++26 form" or names a
  specific revision (C++17, C++20, C++23).

## Reply patterns

When suggesting a C++26 idiom, structure the reply as:

1. The C++26 code (compilable per the standard, even if the local
   compiler lacks support).
2. A one-line "this uses *<feature>* — see [P####] (refs available
   via `cpp26-ref`)".
3. If the local toolchain is below the threshold the
   `check_toolchain` hook reported, a single sentence on compiler
   readiness: "clang 22 / gcc 16 may not compile this yet — install
   `bloomberg/clang-p2996` for reflection demos." Keep this **after**
   the suggestion, never gate-before.

When the user asks "why this instead of X?", quote the relevant row
from the decision table above and link to the reference file by path.

## Companion artefacts

- Reference corpus: `corpus/references/` (216 papers; 16 deep
  hand-curated, 52 shallow templated, 148 stubs).
- Index of all papers: `corpus/index.yaml`.
- Compiler-status matrix: `corpus/status.yaml` (deep tier only).
- Anti-pattern regex source: `tools/cpp26_lint/patterns.yaml`.
- Reviewer subagent: `@cpp26-reviewer` (two-pass: regex anti-pattern
  check + `clang -std=c++2c -fsyntax-only` with bug-vs-lag
  classification).
