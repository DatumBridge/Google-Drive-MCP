"""Shared helpers for MCP tool modules."""

from typing import Optional

from app.core.exceptions import DriveError, GoogleWorkspaceError
from app.schemas.common import CREDENTIALS_REQUIRED_ERROR
from app.services.drive_service import DriveService
from app.services.docs_service import DocsService
from app.services.sheets_service import SheetsService
from app.services.slides_service import SlidesService
from app.services.forms_service import FormsService
from app.services.diagram_service import DiagramService


def credentials_missing(
    credentials_path: Optional[str], credentials_json: Optional[str]
) -> bool:
    return not credentials_path and not credentials_json


def error_dict(error: GoogleWorkspaceError) -> dict:
    return error.to_dict()


def get_drive(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> DriveService:
    return DriveService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


def get_docs(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> DocsService:
    return DocsService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


def get_sheets(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> SheetsService:
    return SheetsService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


def get_slides(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> SlidesService:
    return SlidesService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


def get_forms(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> FormsService:
    return FormsService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


def get_diagrams(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> DiagramService:
    return DiagramService(
        credentials_path=credentials_path, credentials_json=credentials_json
    )


__all__ = [
    "CREDENTIALS_REQUIRED_ERROR",
    "DriveError",
    "GoogleWorkspaceError",
    "credentials_missing",
    "error_dict",
    "get_drive",
    "get_docs",
    "get_sheets",
    "get_slides",
    "get_forms",
    "get_diagrams",
]
