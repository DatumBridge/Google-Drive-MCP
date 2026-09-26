"""draw.io diagram MCP tools (Drive file-based)."""

import logging
from typing import Optional

from pydantic import Field

from app.schemas.diagrams import (
    CreateDiagramResponse,
    ExportDiagramResponse,
    ListDiagramsResponse,
    ReadDiagramResponse,
    UpdateDiagramResponse,
)
from app.tools.common import (
    CREDENTIALS_REQUIRED_ERROR,
    DriveError,
    credentials_missing,
    error_dict,
    get_diagrams,
)

logger = logging.getLogger(__name__)


def register(mcp) -> None:
    @mcp.tool()
    def create_diagram(
        name: str = Field(default="Untitled.drawio", description="Diagram file name"),
        content_xml: Optional[str] = Field(
            default=None, description="Optional mxfile XML; defaults to empty diagram",
        json_schema_extra={"x-datumbridge-encoding": "plain"}
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
        parent_folder_id: Optional[str] = Field(default=None, description="Optional Drive parent folder ID"),
    ) -> CreateDiagramResponse:
        """Create a draw.io (.drawio) diagram file in Google Drive.

        Capabilities: drive.create_diagram
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return CreateDiagramResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_diagrams(credentials_path, credentials_json).create_diagram(
                name=name, parent_folder_id=parent_folder_id, content_xml=content_xml
            )
            return CreateDiagramResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"create_diagram failed: {e.message}")
            return CreateDiagramResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def list_diagrams(
        folder_id: Optional[str] = Field(default=None, description="Folder ID (omit for root)"),
        page_size: int = Field(default=100, description="Max items per page"),
        page_token: Optional[str] = Field(default=None, description="Pagination token"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ListDiagramsResponse:
        """List draw.io diagram files in Drive (MIME/name heuristics).

        Capabilities: drive.list_diagrams
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ListDiagramsResponse(
                    success=False, files=[], total_count=0, error=CREDENTIALS_REQUIRED_ERROR
                )
            files, next_token = get_diagrams(credentials_path, credentials_json).list_diagrams(
                folder_id=folder_id, page_size=page_size, page_token=page_token
            )
            return ListDiagramsResponse(
                success=True,
                files=files,
                total_count=len(files),
                next_page_token=next_token,
            )
        except DriveError as e:
            logger.error(f"list_diagrams failed: {e.message}")
            return ListDiagramsResponse(
                success=False, files=[], total_count=0, error=error_dict(e)
            )

    @mcp.tool()
    def read_diagram(
        file_id: str = Field(..., description="Drive file ID of the .drawio diagram"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReadDiagramResponse:
        """Download draw.io diagram XML/content from Drive.

        Capabilities: drive.read_diagram
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReadDiagramResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_diagrams(credentials_path, credentials_json).read_diagram(file_id)
            return ReadDiagramResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"read_diagram failed: {e.message}")
            return ReadDiagramResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def update_diagram(
        file_id: str = Field(..., description="Drive file ID of the .drawio diagram"),
        content_xml: Optional[str] = Field(default=None, description="New mxfile XML content", json_schema_extra={"x-datumbridge-encoding": "plain"}),
        content_base64: Optional[str] = Field(
            default=None, description="New content as base64 (alternative to content_xml)",
        json_schema_extra={"x-datumbridge-encoding": "base64"}
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> UpdateDiagramResponse:
        """Overwrite draw.io diagram file content in Drive.

        Capabilities: drive.update_diagram
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return UpdateDiagramResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_diagrams(credentials_path, credentials_json).update_diagram(
                file_id, content_xml=content_xml, content_base64=content_base64
            )
            return UpdateDiagramResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"update_diagram failed: {e.message}")
            return UpdateDiagramResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def export_diagram(
        file_id: str = Field(..., description="Drive file ID of the .drawio diagram"),
        export_format: str = Field(
            default="xml",
            description="xml (default). PNG/PDF conversion is not available server-side.",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ExportDiagramResponse:
        """Export diagram content. Server returns XML; no diagrams.net render API.

        Capabilities: drive.export_diagram
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ExportDiagramResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_diagrams(credentials_path, credentials_json).export_diagram(
                file_id, export_format=export_format
            )
            return ExportDiagramResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"export_diagram failed: {e.message}")
            return ExportDiagramResponse(success=False, error=error_dict(e))
