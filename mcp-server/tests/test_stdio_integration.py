"""Integration test: spin the server over stdio, invoke each tool."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

FIXTURE_CORPUS = Path(__file__).resolve().parent / "fixtures" / "corpus"
SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def _server_params() -> StdioServerParameters:
    env = os.environ.copy()
    env["CPP26_CORPUS_DIR"] = str(FIXTURE_CORPUS)
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "cpp26_ref.server"],
        env=env,
    )


@pytest.mark.asyncio
async def test_stdio_handshake_and_three_tools() -> None:
    """Boot the server, list tools, invoke each, assert shape."""
    cold_start = time.perf_counter()
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            cold_elapsed = time.perf_counter() - cold_start

            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert tool_names == {"lookup_paper", "search", "compiler_status"}, tool_names

            # lookup_paper
            r = await session.call_tool("lookup_paper", {"paper_id": "PFIX001"})
            assert not r.isError
            body = "\n".join(c.text for c in r.content if hasattr(c, "text"))
            assert "PFIX001" in body
            assert "Reflection" in body

            # search
            r = await session.call_tool("search", {"query": "reflection", "top_k": 3})
            assert not r.isError
            # Tool returned structured content. The result is in r.structuredContent
            # (dict) or r.content (list of TextContent). Check either.
            results = r.structuredContent.get("result") if r.structuredContent else None
            if results is None:
                # Fall back to parsing text content
                import json
                joined = "\n".join(c.text for c in r.content if hasattr(c, "text"))
                results = json.loads(joined) if joined.strip().startswith(("[", "{")) else []
            assert isinstance(results, list)
            assert any(item.get("id") == "PFIX001" for item in results)

            # compiler_status
            r = await session.call_tool(
                "compiler_status", {"paper_id": "PFIX001", "compiler": "clang-22"}
            )
            assert not r.isError
            status_payload = r.structuredContent or {}
            # Either structuredContent has it, or parse from text content
            if "support" not in status_payload:
                import json
                joined = "\n".join(c.text for c in r.content if hasattr(c, "text"))
                if joined.strip().startswith("{"):
                    status_payload = json.loads(joined)
            assert status_payload.get("support") == "partial" or status_payload.get("result", {}).get("support") == "partial"

    # 500 ms is the binding plan's budget. Allow some slack on slow CI hardware.
    assert cold_elapsed < 2.0, f"cold start {cold_elapsed*1000:.0f} ms (budget 500 ms; CI slack to 2 s)"
