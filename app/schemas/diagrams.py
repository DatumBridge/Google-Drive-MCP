"""Pydantic models for draw.io / diagram MCP tools."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ErrorResponse
from app.schemas.drive import FileMetadata


class CreateDiagramResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    web_view_link: Optional[str] = None
    parent_applied: Optional[bool] = None
    parent_error: Optional[ErrorResponse] = None
    error: Optional[ErrorResponse] = None


class ListDiagramsResponse(BaseModel):
    success: bool
    files: List[FileMetadata] = Field(default_factory=list)
    total_count: int = 0
    next_page_token: Optional[str] = None
    error: Optional[dict] = None


class ReadDiagramResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    content_xml: Optional[str] = None
    content_base64: Optional[str] = None
    truncated: Optional[bool] = None
    error: Optional[ErrorResponse] = None


class UpdateDiagramResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    message: Optional[str] = None
    error: Optional[dict] = None


class ExportDiagramResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    mime_type: Optional[str] = None
    content_xml: Optional[str] = None
    content_base64: Optional[str] = None
    note: Optional[str] = None
    error: Optional[dict] = None
