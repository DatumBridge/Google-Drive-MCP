"""
Google Drive / Workspace MCP Server

Exposes Google Drive + Docs/Sheets/Slides/Forms/draw.io capabilities via MCP.
Uses fastmcp for MCP server implementation.

Usage:
    python -m app.mcp_server
    uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
"""

import logging
from pathlib import Path

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route

from app.oauth_routes import oauth_callback, oauth_info, oauth_start, oauth_token
from app.tools import register_all

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="google-drive",
    instructions="""
    Google Drive MCP Server provides tools for:
    - Drive: upload, download, list, create folder, move, delete, metadata
    - Docs: create, read, append, replace, insert, export
    - Sheets: create, tabs, read/update/append/clear ranges, export
    - Slides: create, list/read, add slide, insert/replace text, export
    - Forms: create, get, update info, add question, list/get responses
    - draw.io: create/list/read/update/export diagram files in Drive

    Credentials must be passed as input: credentials_path or credentials_json.
    Existing drive-only tokens must re-consent for Docs/Sheets/Slides/Forms scopes.
    """,
)

register_all(mcp)

# ============== HTTP App with Health Endpoint ==============

_base_app = mcp.http_app()


async def health(request):
    return JSONResponse({"status": "ok", "service": "google-drive-mcp"})


async def test_ui(request):
    """Serve the manual test UI for MCP tools."""
    ui_path = Path(__file__).resolve().parent.parent / "static" / "test-ui.html"
    if not ui_path.exists():
        return JSONResponse({"error": "test-ui.html not found"}, status_code=404)
    return FileResponse(ui_path, media_type="text/html")


http_app = Starlette(
    routes=[
        Route("/health", health),
        Route("/test", test_ui),
        Route("/oauth/start", oauth_start),
        Route("/oauth/callback", oauth_callback),
        Route("/oauth/token", oauth_token),
        Route("/oauth/info", oauth_info),
        Mount("/", _base_app),
    ],
    lifespan=getattr(_base_app, "lifespan", None),
)


if __name__ == "__main__":
    logger.info("Starting Google Drive MCP Server (stdio mode)")
    mcp.run()
