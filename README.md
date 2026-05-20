# cpp26-adapter

A Claude Code plugin that turns a general-purpose LLM into a C++26 specialist.

The base LLM does general code reasoning; this plugin stacks four layers on top — a knowledge corpus, an MCP reference server, an idiom-bias skill, and a verification subagent — that together bias generation toward C++26 final-form constructs as documented in **ISO/IEC 14882:2026**.

## Core policy

**Recommendations follow the standard, not the toolchain.** If `clang 22` / `gcc 16` don't yet implement a feature, that's not the plugin's problem. The C++26 form is suggested; compiler errors are surfaced as informational *"compiler-lag"* classifications, never as bugs to fix.

## Status

Pre-implementation. See [`PLAN.md`](PLAN.md) for the binding implementation plan.

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

## Install (once built)

```
/plugin install cpp26-adapter@parasxos/claude-plugins
```

## License

- **Code** (everything outside `corpus/`): MIT — see [`LICENSE-CODE`](LICENSE-CODE).
- **Knowledge corpus** (`corpus/`): CC BY-SA 4.0 — see [`LICENSE-CORPUS`](LICENSE-CORPUS).
