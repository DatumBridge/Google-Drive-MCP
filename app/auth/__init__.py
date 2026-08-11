"""Shared Google OAuth credential loading and API client factory."""

from app.auth.scopes import SCOPES
from app.auth.credentials import get_credentials
from app.auth.clients import (
    build_drive_service,
    build_docs_service,
    build_sheets_service,
    build_slides_service,
    build_forms_service,
)

__all__ = [
    "SCOPES",
    "get_credentials",
    "build_drive_service",
    "build_docs_service",
    "build_sheets_service",
    "build_slides_service",
    "build_forms_service",
]
