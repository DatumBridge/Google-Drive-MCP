#!/bin/bash
# Run MCP tools tests.
# Requires: Docker with google-drive-mcp image, and the MCP server container running.
#
# Usage:
#   ./scripts/run_tests.sh                      # structure validation only
#   ./scripts/run_tests.sh token.json           # full integration with OAuth token
#
# For full integration: pass path to OAuth token (from Connect with Google or oauth_connect.py).
# The server container must have the token mounted at the same path.

set -e
cd "$(dirname "$0")/.."

CONTAINER_NAME="${MCP_CONTAINER:-google-drive-mcp}"
TOKEN_PATH="$1"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Error: Container '$CONTAINER_NAME' is not running."
  echo "Start it with: docker run -d -p 8000:8000 --name $CONTAINER_NAME google-drive-mcp"
  exit 1
fi

if [ -n "$TOKEN_PATH" ]; then
  if [ ! -f "$TOKEN_PATH" ]; then
    echo "Error: OAuth token file not found: $TOKEN_PATH"
    exit 1
  fi
  MOUNT_PATH="/token.json"
  docker run --rm --network "container:${CONTAINER_NAME}" \
    -v "${TOKEN_PATH}:${MOUNT_PATH}:ro" \
    google-drive-mcp python scripts/test_mcp_tools.py --credentials-path "${MOUNT_PATH}"
else
  docker run --rm --network "container:${CONTAINER_NAME}" \
    google-drive-mcp python scripts/test_mcp_tools.py
fi
