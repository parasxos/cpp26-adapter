# Dockerfile for Glama MCP introspection checks.
# Builds and runs the cpp26-ref MCP server over stdio.
#
# Glama spawns this container, sends an MCP initialize + list_tools
# request, and reads the response. The corpus is bundled at /app/corpus
# so search and lookup_paper return real data even in the sandboxed run.

FROM python:3.12-slim

WORKDIR /app

# Server source and corpus content.
COPY mcp-server/ /app/mcp-server/
COPY corpus/ /app/corpus/

# Install the cpp26-ref package and its runtime deps
# (mcp, pyyaml, pydantic, rapidfuzz) from the local pyproject.
RUN pip install --no-cache-dir /app/mcp-server

# Point the server at the bundled corpus.
ENV CPP26_CORPUS_DIR=/app/corpus

# stdio transport — the container's stdin/stdout are the MCP channel.
ENTRYPOINT ["cpp26-ref"]
