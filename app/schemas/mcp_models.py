"""
Pydantic models for Google Drive MCP Server tools.

Provides strongly-typed input/output schemas per design spec.
DatumBridge ADK uses these to generate Test UI.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ============== File Metadata ==============


class FileMetadata(BaseModel):
    """Metadata for a Google Drive file or folder."""

    id: str = Field(..., description="Google Drive file ID")
    name: str = Field(..., description="File or folder name")
    mime_type: str = Field(..., description="MIME type (e.g., application/pdf, folder)")
    size: Optional[int] = Field(default=None, description="File size in bytes (null for folders)")
    created_time: Optional[str] = Field(default=None, description="Creation timestamp (ISO 8601)")
    modified_time: Optional[str] = Field(default=None, description="Last modified timestamp (ISO 8601)")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    web_view_link: Optional[str] = Field(default=None, description="URL to view file in browser")
    is_folder: bool = Field(default=False, description="True if this is a folder")


# ============== Tool Response Models ==============


class FileListResponse(BaseModel):
    """Response from list_files tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    files: List[FileMetadata] = Field(default_factory=list, description="List of files/folders")
    total_count: int = Field(default=0, description="Number of items returned")
    next_page_token: Optional[str] = Field(default=None, description="Token for pagination")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class UploadResponse(BaseModel):
    """Response from upload_file tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    file_id: Optional[str] = Field(default=None, description="ID of uploaded file")
    file_name: Optional[str] = Field(default=None, description="Name of uploaded file")
    web_view_link: Optional[str] = Field(default=None, description="URL to view file")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class DownloadResponse(BaseModel):
    """Response from download_file tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    file_id: Optional[str] = Field(default=None, description="ID of downloaded file")
    file_name: Optional[str] = Field(default=None, description="Name of file")
    content_base64: Optional[str] = Field(default=None, description="File content as base64 (for binary)")
    content_text: Optional[str] = Field(default=None, description="File content as text (for text files)")
    mime_type: Optional[str] = Field(default=None, description="MIME type of file")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class CreateFolderResponse(BaseModel):
    """Response from create_folder tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    folder_id: Optional[str] = Field(default=None, description="ID of created folder")
    folder_name: Optional[str] = Field(default=None, description="Name of folder")
    web_view_link: Optional[str] = Field(default=None, description="URL to view folder")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class MoveResponse(BaseModel):
    """Response from move_file tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    file_id: Optional[str] = Field(default=None, description="ID of moved file")
    new_parent_id: Optional[str] = Field(default=None, description="New parent folder ID")
    message: Optional[str] = Field(default=None, description="Status message")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class DeleteResponse(BaseModel):
    """Response from delete_file tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    file_id: Optional[str] = Field(default=None, description="ID of deleted file")
    message: Optional[str] = Field(default=None, description="Status message")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class GetMetadataResponse(BaseModel):
    """Response from get_file_metadata tool."""

    success: bool = Field(..., description="Whether operation succeeded")
    metadata: Optional[FileMetadata] = Field(default=None, description="File metadata")
    error: Optional[dict] = Field(default=None, description="Error details if success=False")


class ErrorResponse(BaseModel):
    """Standardized error structure for MCP."""

    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    retryable: bool = Field(default=False, description="Whether client should retry")
    original_provider_error: Optional[str] = Field(default=None, description="Original Google API error")
