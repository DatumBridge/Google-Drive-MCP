"""Google Docs MCP tools."""

import base64
import logging
from typing import Optional

from pydantic import Field

from app.schemas.docs import (
    AppendDocumentTextResponse,
    CreateDocumentResponse,
    ExportDocumentResponse,
    InsertDocumentTextResponse,
    ReadDocumentResponse,
    ReplaceDocumentTextResponse,
)
from app.tools.common import (
    CREDENTIALS_REQUIRED_ERROR,
    DriveError,
    credentials_missing,
    error_dict,
    get_docs,
)

logger = logging.getLogger(__name__)


def register(mcp) -> None:
    @mcp.tool()
    def create_document(
        title: str = Field(default="Untitled document", description="Document title"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
        parent_folder_id: Optional[str] = Field(default=None, description="Optional Drive parent folder ID"),
    ) -> CreateDocumentResponse:
        """Create a Google Doc. Optionally move it into a Drive folder (parent_applied reports success)."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return CreateDocumentResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_docs(credentials_path, credentials_json).create_document(
                title=title, parent_folder_id=parent_folder_id
            )
            return CreateDocumentResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"create_document failed: {e.message}")
            return CreateDocumentResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def read_document(
        document_id: str = Field(..., description="Google Docs document ID"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReadDocumentResponse:
        """Read a Google Doc as plain text."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReadDocumentResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_docs(credentials_path, credentials_json).read_document(document_id)
            return ReadDocumentResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"read_document failed: {e.message}")
            return ReadDocumentResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def append_document_text(
        document_id: str = Field(..., description="Google Docs document ID"),
        text: str = Field(..., description="Text to append at the end of the document"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> AppendDocumentTextResponse:
        """Append text to the end of a Google Doc (hides raw index math)."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return AppendDocumentTextResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            get_docs(credentials_path, credentials_json).append_text(document_id, text)
            return AppendDocumentTextResponse(
                success=True, document_id=document_id, message="Text appended"
            )
        except DriveError as e:
            logger.error(f"append_document_text failed: {e.message}")
            return AppendDocumentTextResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def replace_document_text(
        document_id: str = Field(..., description="Google Docs document ID"),
        find_text: str = Field(..., description="Text to find"),
        replace_text: str = Field(..., description="Replacement text"),
        match_case: bool = Field(default=True, description="Case-sensitive match"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReplaceDocumentTextResponse:
        """Find and replace all matching text in a Google Doc."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReplaceDocumentTextResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            count = get_docs(credentials_path, credentials_json).replace_text(
                document_id, find_text, replace_text, match_case=match_case
            )
            return ReplaceDocumentTextResponse(
                success=True,
                document_id=document_id,
                occurrences_changed=count,
                message=f"Replaced {count} occurrence(s)",
            )
        except DriveError as e:
            logger.error(f"replace_document_text failed: {e.message}")
            return ReplaceDocumentTextResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def insert_document_text(
        document_id: str = Field(..., description="Google Docs document ID"),
        text: str = Field(..., description="Text to insert"),
        index: Optional[int] = Field(
            default=None,
            description="Optional Docs body index (>=1). Omit to append at end.",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> InsertDocumentTextResponse:
        """Insert text at an optional Docs index, or append when index is omitted."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return InsertDocumentTextResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            get_docs(credentials_path, credentials_json).insert_text(document_id, text, index=index)
            return InsertDocumentTextResponse(
                success=True, document_id=document_id, message="Text inserted"
            )
        except DriveError as e:
            logger.error(f"insert_document_text failed: {e.message}")
            return InsertDocumentTextResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def export_document(
        document_id: str = Field(..., description="Google Docs document ID"),
        export_format: str = Field(
            default="text/plain",
            description="Export format: text/plain, application/pdf, or docx",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ExportDocumentResponse:
        """Export a Google Doc via Drive export (plain text, PDF, or DOCX)."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ExportDocumentResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            content, mime = get_docs(credentials_path, credentials_json).export_document(
                document_id, export_format
            )
            if mime.startswith("text/"):
                return ExportDocumentResponse(
                    success=True,
                    document_id=document_id,
                    mime_type=mime,
                    content_text=content.decode("utf-8", errors="replace"),
                )
            return ExportDocumentResponse(
                success=True,
                document_id=document_id,
                mime_type=mime,
                content_base64=base64.b64encode(content).decode("ascii"),
            )
        except DriveError as e:
            logger.error(f"export_document failed: {e.message}")
            return ExportDocumentResponse(success=False, error=error_dict(e))
