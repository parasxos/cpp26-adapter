# cpp26-adapter

A Claude Code plugin that turns a general-purpose LLM into a C++26 specialist.

The base LLM does general code reasoning; this plugin stacks four layers on top — a knowledge corpus, an MCP reference server, an idiom-bias skill, and a verification subagent — that together bias generation toward C++26 final-form constructs as documented in **ISO/IEC 14882:2026**.

## Core policy

**Recommendations follow the standard, not the toolchain.** If `clang 22` / `gcc 16` don't yet implement a feature, that's not the plugin's problem. The C++26 form is suggested; compiler errors are surfaced as informational *"compiler-lag"* classifications, never as bugs to fix.

## Status

**v0.9.0 — feature-complete, eval gate cleared.**
On the held 39-task suite, the plugin scores **37/39 (95%) standard-compliance**
— well above the v1.0 gate (≥85%). See [`eval/results-v0.9.0.md`](eval/results-v0.9.0.md)
for the per-task breakdown. The implementation history is in [`PLAN.md`](PLAN.md);
the standard-first architecture is in [`docs/architecture.md`](docs/architecture.md).

## What's inside

- **Skill `cpp26-idioms`** — constitution + 20-row decision table mapping
  pre-C++26 idioms to their C++26 successors (`assert` → `contract_assert`,
  `magic_enum` → reflection, `std::async` → `std::execution` senders, …).
- **MCP server `cpp26-ref`** — three stdio tools (`lookup_paper`, `search`,
  `compiler_status`) backed by a 216-paper corpus (16 hand-curated deep,
  52 templated shallow, 148 stubs).
- **Subagent `@cpp26-reviewer`** — two-pass review: Pass 1 regex anti-pattern
  scan, Pass 2 `clang -std=c++2c -fsyntax-only` with bug-vs-compiler-lag
  classification routed through the MCP.
- **Hook surface** — SessionStart toolchain probe (warns if clang < 22 /
  gcc < 16) and PostToolUse Pass-1 lint on any C++ file edit.
- **Slash command `/cpp26-init`** — scaffolds a C++26-ready `CMakeLists.txt`,
  `.clangd`, and per-project overrides.

## Layout

```
.claude-plugin/   plugin.json manifest
agents/           cpp26-reviewer subagent (two-pass: regex + clang -fsyntax-only)
skills/           cpp26-idioms — the constitution + decision table
hooks/            PostToolUse (anti-pattern lint) + SessionStart (toolchain probe)
commands/         /cpp26-init slash command
mcp-server/       cpp26-ref MCP server (3 stdio tools, in-memory)
corpus/           the C++26 knowledge base (index.yaml, references/, status.yaml)
tools/            regex anti-pattern lint + helper scripts
eval/             eval suite + harness (added in Phase 7)
```

## Install

From the personal marketplace:

```
/plugin install cpp26-adapter@parasxos/claude-plugins
```

Or from a local clone (development):

```bash
git clone https://github.com/parasxos/claude-plugins.git
cd claude-plugins/cpp26-adapter
mcp-server/.venv/bin/pip install -e mcp-server   # one-time MCP setup
claude --plugin-dir .                            # load the plugin in this session
```

## Verifying the install

A clean install should make the following work without further setup:

1. Ask Claude to *"write enum-to-string for `enum class E { A, B }`"* in any
   C++ context — the response should use `std::meta` reflection, not X-macros
   or `magic_enum`.
2. `@cpp26-reviewer src/foo.cpp` should produce a YAML report with
   `status: pass | needs-changes | compiler-lag-only`.
3. `/cpp26-init` in an empty directory should scaffold a buildable
   `CMakeLists.txt` (`cmake -B build && cmake --build build` must succeed
   given a `main.cpp` containing `#include <print>` + `std::print("hi\n")`).

## License

- **Code** (everything outside `corpus/`): MIT — see [`LICENSE-CODE`](LICENSE-CODE).
- **Knowledge corpus** (`corpus/`): CC BY-SA 4.0 — see [`LICENSE-CORPUS`](LICENSE-CORPUS).
