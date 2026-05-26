# cpp26-adapter

**Turn your LLM coding assistant into a C++26 specialist.**
A Claude Code plugin (and standalone MCP server) that biases generation toward ISO/IEC 14882:2026 final-form idioms — reflection, contracts, senders, `inplace_vector`, `#embed` — even when your local clang hasn't caught up.

[![ci](https://github.com/parasxos/cpp26-adapter/actions/workflows/ci.yml/badge.svg)](https://github.com/parasxos/cpp26-adapter/actions/workflows/ci.yml)
[![version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/parasxos/cpp26-adapter/releases/tag/v1.0.0)
[![pypi](https://img.shields.io/pypi/v/cpp26-ref?label=cpp26-ref)](https://pypi.org/project/cpp26-ref/)
[![eval](https://img.shields.io/badge/eval-35%2F39%20(90%25)-brightgreen)](eval/results-v0.9.1.md)
[![bar](https://img.shields.io/badge/bar-%E2%89%A585%25-success)](eval/results-v0.9.1.md)
[![standard](https://img.shields.io/badge/ISO%2FIEC-14882%3A2026-orange)](https://www.iso.org/standard/83626.html)
[![code license](https://img.shields.io/badge/code-MIT-green)](LICENSE-CODE)

## Quick Start

**Full plugin** (Claude Code — skill + MCP + reviewer + hooks + slash command):

```
/plugin marketplace add parasxos/claude-plugins
/plugin install cpp26-adapter@parasxos/claude-plugins
```

**MCP server only** (any MCP-compatible client):

```bash
pip install cpp26-ref
```

## What it does

Six concrete idiom shifts on the same prompts a vanilla LLM would answer with pre-C++26 patterns:

| You ask for… | Vanilla LLM emits | `cpp26-adapter` emits |
|---|---|---|
| enum → string | X-macros / `magic_enum` | `std::meta::enumerators_of(^^E)` + `template for` |
| precondition | `assert(x > 0)` | `pre(x > 0)` / `contract_assert(...)` |
| async pipeline | `std::async(...)` | `ex::just \| ex::then \| ex::sync_wait` |
| fixed-capacity vector | `boost::static_vector` | `std::inplace_vector<T, N>` |
| embed binary asset | `objcopy` / `xxd` / `incbin` | `#embed "asset.bin"` |
| Nth pack element | `std::get<N>(std::forward_as_tuple(args...))` | `args...[N]` |

### The hook — ask for "enum to string"

Vanilla falls back to X-macros. With `cpp26-adapter` — straight from P2996 reflection + P1306 expansion statements:

```cpp
template <typename E> requires std::is_enum_v<E>
constexpr std::string_view enum_name(E v) {
    template for (constexpr auto e :
                  std::define_static_array(std::meta::enumerators_of(^^E))) {
        if (v == [: e :]) return std::meta::identifier_of(e);
    }
    return "<unknown>";
}
```

No macros. No third-party dep. No codegen. More side-by-side examples (contracts, senders, `#embed`): [`docs/examples.md`](docs/examples.md).

## Compatible clients

| Client | Recommended path |
|---|---|
| Claude Code | `/plugin install` (full plugin: skill + MCP + reviewer + hooks) |
| Claude Desktop | `cpp26-ref` MCP server via stdio (config below) |
| Cursor | `cpp26-ref` MCP server via stdio |
| VS Code (Cline / Continue) | `cpp26-ref` MCP server via stdio |
| Any other MCP client | `cpp26-ref` MCP server via stdio |

## Configuration

### Claude Code

After `/plugin install cpp26-adapter@parasxos/claude-plugins`, everything wires itself up: the skill loads into context, the MCP starts on demand, the reviewer subagent is callable as `@cpp26-reviewer`, the hook lints on every C++ edit, and `/cpp26-init` is available.

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "cpp26-ref": {
      "command": "cpp26-ref"
    }
  }
}
```

Requires `pip install cpp26-ref` on a Python (≥3.11) reachable from the Claude Desktop process.

### Cursor / VS Code / generic MCP client

```json
{
  "mcpServers": {
    "cpp26-ref": { "command": "cpp26-ref" }
  }
}
```

### Verify the install

After install + restart, three sanity checks:

1. Ask the assistant *"write enum-to-string for `enum class E { A, B }`"* — the response should use `std::meta` reflection, not X-macros or `magic_enum`.
2. (Full plugin only) Run `@cpp26-reviewer src/foo.cpp` — should return a YAML report with `status: pass | needs-changes | compiler-lag-only`.
3. (Full plugin only) Run `/cpp26-init` in an empty directory — the scaffolded `CMakeLists.txt` should build a `#include <print>` + `std::print("hi\n")` hello-world.

## MCP tools

The `cpp26-ref` server exposes three stdio tools over MCP, in-memory over 216 indexed C++26 papers (no SQLite, no embeddings, no build step):

| Tool | Signature | Returns |
|---|---|---|
| `lookup_paper` | `(paper_id: str)` — e.g. `"P2996"` | Full reference: title, problem statement, key syntax, canonical example, pre-C++26 equivalent, gotchas, related papers |
| `search` | `(query: str, limit: int = 5)` | Top-N papers ranked by `rapidfuzz` partial-ratio against title + frontmatter |
| `compiler_status` | `(paper_id: str)` | Per-compiler implementation status: `none`/`partial`/`shipped` × `clang` / `gcc` / `msvc` / `clang-p2996` with version cutoffs |

Cold start ~352 ms. 17 tests pass under `pytest mcp-server/tests`.

## Use cases

**Generate idiomatic C++26 code.** Ask for new code — the skill biases the model toward the C++26 idiom before generation, so you get `pre(...)` instead of `assert(...)`, `std::execution` instead of `std::async`, reflection instead of X-macros, without re-prompting.

**Review existing code for C++26 modernization.** Run `@cpp26-reviewer src/foo.cpp` — the subagent runs a two-pass review: regex anti-patterns first, then `clang -std=c++2c -fsyntax-only`, classifying each diagnostic as `compiler-lag` (paper adopted, compiler incomplete) or `bug` (genuine code error). You see both axes side by side.

**Initialize a new C++26 project.** Run `/cpp26-init` — scaffolds `CMakeLists.txt` (`CXX_STANDARD 26`, `-std=c++2c`, `CMAKE_EXPORT_COMPILE_COMMANDS ON`), `.clangd`, and `.cpp26-adapter.yaml`.

**Get authoritative paper references.** The `lookup_paper` MCP tool returns the canonical paper text — useful when you need to cite or quote a paper, or when you want the LLM to ground its answer in the actual proposal rather than its (often stale) training data.

## The invariant

**Recommendations follow the standard, not the toolchain.** If `clang < 22` / `gcc < 16` haven't shipped a feature, the plugin still suggests the C++26 form. Compiler errors are surfaced as `compiler-lag` or `bug` — never auto-rewritten into a pre-C++26 workaround.

The suggestion path (skill + MCP) is compiler-agnostic; compiler awareness lives only in the reviewer's Pass-2 syntax check and the `SessionStart` probe. Full architecture diagram: [`docs/architecture.md`](docs/architecture.md).

## Eval

37/39 (95%) with plugin **ON** vs 14/39 (36%) **OFF** on a 39-task held suite; bar ≥85%. Per-task scoring + methodology: [`eval/results-v0.9.0.md`](eval/results-v0.9.0.md), [`docs/papers.md`](docs/papers.md).

## Status

**v1.0.0** — eval gate held across two successive refreshes. The MCP tool signatures, the subagent's output schema, and the standard-first invariant are contract-binding for the `1.x` line.

## License

Dual-licensed by directory:

- **Code** (everything outside `corpus/`): MIT — [`LICENSE-CODE`](LICENSE-CODE).
- **Knowledge corpus** (`corpus/`): CC-BY-SA 4.0 — [`LICENSE-CORPUS`](LICENSE-CORPUS).

## See also

- [`docs/architecture.md`](docs/architecture.md) — full invariant, component diagram, walkthrough
- [`docs/examples.md`](docs/examples.md) — contracts, senders, `#embed` side-by-side
- [`docs/papers.md`](docs/papers.md) — the 16 deep-tier papers + eval methodology
- [`docs/FAQ.md`](docs/FAQ.md) — clang/gcc compatibility, legacy code, refresh cadence
- Plugin repo: [github.com/parasxos/cpp26-adapter](https://github.com/parasxos/cpp26-adapter) · Marketplace: [github.com/parasxos/claude-plugins](https://github.com/parasxos/claude-plugins) · PyPI: [pypi.org/project/cpp26-ref](https://pypi.org/project/cpp26-ref/)
