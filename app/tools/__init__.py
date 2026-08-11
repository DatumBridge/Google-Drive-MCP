"""MCP tool registration modules."""

from app.tools import (
    drive_tools,
    docs_tools,
    sheets_tools,
    slides_tools,
    forms_tools,
    diagram_tools,
)


def register_all(mcp) -> None:
    drive_tools.register(mcp)
    docs_tools.register(mcp)
    sheets_tools.register(mcp)
    slides_tools.register(mcp)
    forms_tools.register(mcp)
    diagram_tools.register(mcp)
