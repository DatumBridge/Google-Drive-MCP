"""
Google Drive MCP Server

Exposes Google Drive capabilities via Model Context Protocol (MCP).
Uses fastmcp for MCP server implementation.

Tools: upload_file, download_file, list_files, create_folder, move_file, delete_file, get_file_metadata

Usage:
    # Run as standalone server (stdio mode for Claude Desktop):
    python -m app.mcp_server

    # Or with uvicorn for HTTP/SSE mode:
    uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
"""

import base64
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

from app.schemas.mcp_models import (
    FileListResponse,
    UploadResponse,
    DownloadResponse,
    CreateFolderResponse,
    MoveResponse,
    DeleteResponse,
    GetMetadataResponse,
)
from app.services.drive_service import DriveService
from app.core.exceptions import DriveError

# Initialize MCP Server
mcp = FastMCP(
    name="google-drive",
    instructions="""
    Google Drive MCP Server provides tools for:
    - Uploading files to Google Drive
    - Downloading files from Google Drive
    - Listing files and folders
    - Creating folders
    - Moving files between folders
    - Deleting files
    - Getting file metadata

    Use these tools to manage files in Google Drive as part of workflows.
    Credentials must be passed as input: credentials_path or credentials_json.
    """,
)


def _get_drive_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> DriveService:
    """Create DriveService with credentials from tool input."""
    if not credentials_path and not credentials_json:
        raise ValueError(
            "Credentials required: provide credentials_path or credentials_json"
        )
    return DriveService(
        credentials_path=credentials_path,
        credentials_json=credentials_json,
    )


def _error_response(error: DriveError) -> dict:
    """Build error dict for response models."""
    return error.to_dict()


# ============== Google Drive Tools ==============


@mcp.tool()
def upload_file(
    file_name: str = Field(..., description="Name for the uploaded file"),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file (e.g. token.json from oauth_connect.py). One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
    content_base64: Optional[str] = Field(
        default=None,
        description="File content as base64-encoded string (use for binary or text)",
    ),
    file_path: Optional[str] = Field(
        default=None,
        description="Local file path to upload (when running on server with file access)",
    ),
    parent_folder_id: Optional[str] = Field(
        default=None,
        description="ID of parent folder (omit for root)",
    ),
    mime_type: Optional[str] = Field(
        default=None,
        description="MIME type (e.g., text/plain, application/pdf). Auto-detected from file_path if not provided.",
    ),
) -> UploadResponse:
    """
    Upload a file to Google Drive.
    Provide either content_base64 (for MCP clients) or file_path (for server-side files).
    Credentials must be passed as credentials_path or credentials_json.
    """
    logger.info(f"MCP: Uploading file {file_name}")
    try:
        if not credentials_path and not credentials_json:
            return UploadResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        if not content_base64 and not file_path:
            return UploadResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "Either content_base64 or file_path must be provided",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        result = drive_service.upload_file(
            file_name=file_name,
            content_base64=content_base64,
            file_path=file_path,
            parent_folder_id=parent_folder_id,
            mime_type=mime_type,
        )
        return UploadResponse(
            success=True,
            file_id=result.get("id"),
            file_name=result.get("name"),
            web_view_link=result.get("webViewLink"),
        )
    except DriveError as e:
        logger.error(f"Upload failed: {e.message}")
        return UploadResponse(success=False, error=_error_response(e))


@mcp.tool()
def download_file(
    file_id: str = Field(..., description="Google Drive file ID to download"),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
    as_text: bool = Field(
        default=False,
        description="If true, return content as text. If false, return base64 for binary files.",
    ),
) -> DownloadResponse:
    """
    Download a file from Google Drive by ID.
    Returns content as base64 (default) or plain text for text files.
    """
    logger.info(f"MCP: Downloading file {file_id}")
    try:
        if not credentials_path and not credentials_json:
            return DownloadResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        content_bytes, mime_type, file_name = drive_service.download_file(file_id)
        if as_text and (
            mime_type.startswith("text/")
            or "json" in mime_type
            or "xml" in mime_type
        ):
            content_text = content_bytes.decode("utf-8", errors="replace")
            return DownloadResponse(
                success=True,
                file_id=file_id,
                file_name=file_name,
                content_text=content_text,
                mime_type=mime_type,
            )
        content_base64 = base64.b64encode(content_bytes).decode("ascii")
        return DownloadResponse(
            success=True,
            file_id=file_id,
            file_name=file_name,
            content_base64=content_base64,
            mime_type=mime_type,
        )
    except DriveError as e:
        logger.error(f"Download failed: {e.message}")
        return DownloadResponse(success=False, error=_error_response(e))


@mcp.tool()
def list_files(
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
    folder_id: Optional[str] = Field(
        default=None,
        description="Folder ID to list (omit for root)",
    ),
    page_size: int = Field(default=100, description="Max items per page (1-1000)"),
    page_token: Optional[str] = Field(
        default=None,
        description="Token for next page (from previous list_files response)",
    ),
    query: Optional[str] = Field(
        default=None,
        description="Optional Drive query (e.g., mimeType='application/pdf')",
    ),
) -> FileListResponse:
    """
    List files and folders in a Google Drive folder.
    Returns file metadata including id, name, mimeType, size, timestamps.
    """
    logger.info(f"MCP: Listing files in folder={folder_id}, page_size={page_size}")
    try:
        if not credentials_path and not credentials_json:
            return FileListResponse(
                success=False,
                files=[],
                total_count=0,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        files, next_token = drive_service.list_files(
            folder_id=folder_id,
            page_size=min(max(page_size, 1), 1000),
            page_token=page_token,
            query=query,
        )
        return FileListResponse(
            success=True,
            files=files,
            total_count=len(files),
            next_page_token=next_token,
        )
    except DriveError as e:
        logger.error(f"List files failed: {e.message}")
        return FileListResponse(
            success=False,
            files=[],
            total_count=0,
            error=_error_response(e),
        )


@mcp.tool()
def create_folder(
    folder_name: str = Field(..., description="Name for the new folder"),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
    parent_folder_id: Optional[str] = Field(
        default=None,
        description="Parent folder ID (omit for root)",
    ),
) -> CreateFolderResponse:
    """
    Create a new folder in Google Drive.
    """
    logger.info(f"MCP: Creating folder {folder_name}")
    try:
        if not credentials_path and not credentials_json:
            return CreateFolderResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        result = drive_service.create_folder(
            folder_name=folder_name,
            parent_folder_id=parent_folder_id,
        )
        return CreateFolderResponse(
            success=True,
            folder_id=result.get("id"),
            folder_name=result.get("name"),
            web_view_link=result.get("webViewLink"),
        )
    except DriveError as e:
        logger.error(f"Create folder failed: {e.message}")
        return CreateFolderResponse(success=False, error=_error_response(e))


@mcp.tool()
def move_file(
    file_id: str = Field(..., description="ID of file or folder to move"),
    new_parent_folder_id: str = Field(
        ...,
        description="ID of destination folder",
    ),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
) -> MoveResponse:
    """
    Move a file or folder to a different parent folder.
    """
    logger.info(f"MCP: Moving file {file_id} to folder {new_parent_folder_id}")
    try:
        if not credentials_path and not credentials_json:
            return MoveResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        drive_service.move_file(
            file_id=file_id,
            new_parent_folder_id=new_parent_folder_id,
        )
        return MoveResponse(
            success=True,
            file_id=file_id,
            new_parent_id=new_parent_folder_id,
            message="File moved successfully",
        )
    except DriveError as e:
        logger.error(f"Move file failed: {e.message}")
        return MoveResponse(success=False, error=_error_response(e))


@mcp.tool()
def delete_file(
    file_id: str = Field(..., description="ID of file or folder to delete"),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
) -> DeleteResponse:
    """
    Permanently delete a file or folder from Google Drive.
    This bypasses trash - the file cannot be recovered.
    """
    logger.info(f"MCP: Deleting file {file_id}")
    try:
        if not credentials_path and not credentials_json:
            return DeleteResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        drive_service.delete_file(file_id=file_id)
        return DeleteResponse(
            success=True,
            file_id=file_id,
            message="File deleted successfully",
        )
    except DriveError as e:
        logger.error(f"Delete file failed: {e.message}")
        return DeleteResponse(success=False, error=_error_response(e))


@mcp.tool()
def get_file_metadata(
    file_id: str = Field(..., description="Google Drive file ID"),
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth token JSON file. One of credentials_path or credentials_json required.",
    ),
    credentials_json: Optional[str] = Field(
        default=None,
        description="OAuth token JSON string. One of credentials_path or credentials_json required.",
    ),
) -> GetMetadataResponse:
    """
    Get metadata for a file or folder (name, size, mimeType, timestamps, etc.).
    """
    logger.info(f"MCP: Getting metadata for file {file_id}")
    try:
        if not credentials_path and not credentials_json:
            return GetMetadataResponse(
                success=False,
                error={
                    "error_code": "CREDENTIALS_REQUIRED",
                    "error_message": "Provide credentials_path or credentials_json",
                    "retryable": False,
                    "original_provider_error": None,
                },
            )
        drive_service = _get_drive_service(credentials_path, credentials_json)
        metadata = drive_service.get_metadata(file_id=file_id)
        return GetMetadataResponse(success=True, metadata=metadata)
    except DriveError as e:
        logger.error(f"Get metadata failed: {e.message}")
        return GetMetadataResponse(success=False, error=_error_response(e))


# ============== HTTP App with Health Endpoint ==============

# Create ASGI app for HTTP/SSE transport
_base_app = mcp.http_app()

# Wrap to add /health and test UI - must pass MCP lifespan for Streamable HTTP session manager
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, FileResponse

from app.oauth_routes import oauth_start, oauth_callback, oauth_token, oauth_info


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


# ============== Main Entry Point ==============

if __name__ == "__main__":
    logger.info("Starting Google Drive MCP Server (stdio mode)")
    mcp.run()
