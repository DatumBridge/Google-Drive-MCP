#!/bin/bash
# Entrypoint for running Google Drive MCP Server in HTTP/SSE mode
# Usage: ./mcp_server_entrypoint.sh
# Or: uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000

cd "$(dirname "$0")"
uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
