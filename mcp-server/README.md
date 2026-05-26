# cpp26-ref MCP server

Stdio MCP server that exposes three tools to Claude Code:

| Tool | Purpose |
|---|---|
| `lookup_paper(paper_id)` | Return the full markdown content of `corpus/references/<paper_id>.md`. |
| `search(query, top_k=5)`  | Fuzzy + keyword match over `corpus/index.yaml`. Returns `[{id, title, tier, score, path}]`. |
| `compiler_status(paper_id, compiler=None)` | Read `corpus/status.yaml`. **Informational only** — the skill must not gate on it. |

This package is part of the `cpp26-adapter` Claude Code plugin. See the repo root for the binding plan.

## Local dev

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests
```

## Wire-up

The plugin's `.mcp.json` registers this server as `cpp26-ref` and launches it via stdio.
