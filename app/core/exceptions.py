"""
Error handling for Google Workspace MCP Server.

Normalizes Google API errors into MCP-compatible format:
- error_code
- error_message
- retryable (true/false)
- original_provider_error
"""

from __future__ import annotations

import re
from typing import Optional, Any


class GoogleWorkspaceError(Exception):
    """Base error for Google Workspace / Drive operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "WORKSPACE_ERROR",
        retryable: bool = False,
        original_error: Optional[Any] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.original_error = original_error
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert to standardized error structure for MCP responses."""
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "retryable": self.retryable,
            "original_provider_error": str(self.original_error) if self.original_error else None,
        }


# Backward-compatible alias for existing Drive tooling
DriveError = GoogleWorkspaceError


class DriveAuthError(GoogleWorkspaceError):
    """Authentication/authorization failure (401)."""

    def __init__(self, message: str = "Token expired or invalid. Reconnect Google Drive under Account → Integrations.", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            retryable=True,
            original_error=original_error,
        )


class DriveNotFoundError(GoogleWorkspaceError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            retryable=False,
            original_error=original_error,
        )


class DrivePermissionError(GoogleWorkspaceError):
    """Permission denied (403)."""

    def __init__(self, message: str = "Permission denied", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            retryable=False,
            original_error=original_error,
        )


class DriveRateLimitError(GoogleWorkspaceError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            retryable=True,
            original_error=original_error,
        )


_API_NOT_ENABLED_MARKERS = (
    "service_disabled",
    "access_not_configured",
    "has not been used in project",
    "api has not been used",
)
_AUTH_BLOB_MARKERS = (
    "invalid_grant",
    "token expired",
    "invalid token",
    "invalid credentials",
    "unauthorized",
)
_API_TITLE_RE = re.compile(
    r"(Google (?:Sheets|Drive|Docs|Slides|Forms) API)",
    re.IGNORECASE,
)
_ACTIVATION_URL_RE = re.compile(
    r"https://console\.(?:developers|cloud)\.google\.com/apis/api/[a-z0-9.]+/overview\?project=\d+",
    re.IGNORECASE,
)


def _error_blob(exc: Exception) -> str:
    parts = [str(exc)]
    content = getattr(exc, "content", None)
    if isinstance(content, bytes):
        parts.append(content.decode("utf-8", errors="replace"))
    elif content is not None:
        parts.append(str(content))
    return "\n".join(parts)


def _is_api_not_enabled(blob: str) -> bool:
    lower = blob.lower()
    return any(marker in lower for marker in _API_NOT_ENABLED_MARKERS)


def _is_office_file_error(blob: str) -> bool:
    lower = blob.lower()
    return "must not be an office file" in lower or (
        "not supported for this document" in lower and "office" in lower
    )


def _is_invalid_drive_query(blob: str) -> bool:
    """Drive files.list 400 Invalid Value on q — not an OAuth failure."""
    lower = blob.lower()
    if "invalid value" not in lower and "reason': 'invalid'" not in lower and 'reason": "invalid"' not in lower:
        return False
    return (
        "location': 'q'" in lower
        or 'location": "q"' in lower
        or ("/drive/v3/files" in lower and "q=" in lower)
    )


def _invalid_drive_query_error(exc: Exception, blob: str) -> GoogleWorkspaceError:
    original = blob.strip().split("\n", 1)[0]
    return GoogleWorkspaceError(
        message=(
            "Google Drive list_files query (q) is invalid. "
            "Drive search is not free text — use syntax such as "
            "name contains 'Budget' or mimeType='application/vnd.google-apps.spreadsheet'. "
            f"Original: {original}"
        ),
        error_code="INVALID_QUERY",
        retryable=False,
        original_error=exc,
    )


def _is_auth_blob(blob: str) -> bool:
    lower = blob.lower()
    if any(marker in lower for marker in _AUTH_BLOB_MARKERS):
        return True
    # Do not treat pageToken= in the request URL as an OAuth token.
    return bool(re.search(r"\b401\b", lower)) and "invalid value" not in lower


def _api_not_enabled_error(exc: Exception, blob: str) -> GoogleWorkspaceError:
    api = "Google API"
    title = _API_TITLE_RE.search(blob)
    if title:
        api = title.group(1)
    url_match = _ACTIVATION_URL_RE.search(blob)
    url = (
        url_match.group(0)
        if url_match
        else "https://console.cloud.google.com/apis/library"
    )
    message = (
        f"{api} is not enabled on this Google Cloud OAuth project. "
        f"In Google Cloud Console enable {api}, wait a few minutes, then retry. "
        f"Activation: {url}. "
        "This is not a Drive sharing ACL and not a missing OAuth reconnect."
    )
    return GoogleWorkspaceError(
        message=message,
        error_code="API_NOT_ENABLED",
        retryable=True,
        original_error=exc,
    )


def normalize_google_error(exc: Exception) -> GoogleWorkspaceError:
    """
    Map Google API HTTP errors to standardized GoogleWorkspaceError subclasses.
    Prefer HttpError.resp.status when available; fall back to message parsing.
    """
    blob = _error_blob(exc)
    if _is_api_not_enabled(blob):
        return _api_not_enabled_error(exc, blob)
    if _is_office_file_error(blob):
        return GoogleWorkspaceError(
            message=(
                "This Drive file is a Microsoft Excel/Office workbook, not a native "
                "Google Sheet. In Drive, Open with → Google Sheets, then use the new "
                "file id as spreadsheet_id. The Sheets API cannot read .xlsx file ids."
            ),
            error_code="OFFICE_FILE_NOT_SUPPORTED",
            retryable=False,
            original_error=exc,
        )
    if _is_invalid_drive_query(blob):
        return _invalid_drive_query_error(exc, blob)

    status = None
    resp = getattr(exc, "resp", None)
    if resp is not None:
        status = getattr(resp, "status", None)
        if status is not None:
            try:
                status = int(status)
            except (TypeError, ValueError):
                status = None

    if status == 400:
        if _is_invalid_drive_query(blob):
            return _invalid_drive_query_error(exc, blob)
        return GoogleWorkspaceError(
            message=str(exc),
            error_code="VALIDATION_ERROR",
            retryable=False,
            original_error=exc,
        )
    if status == 401:
        return DriveAuthError(
            message=(
                "Google Drive token expired or invalid. "
                "Reconnect Google Drive under Studio Account → Integrations, then retry."
            ),
            original_error=exc,
        )
    if status == 403:
        return DrivePermissionError(message="Permission denied", original_error=exc)
    if status == 404:
        return DriveNotFoundError(message="Resource not found", original_error=exc)
    if status == 429:
        return DriveRateLimitError(message="Rate limit exceeded", original_error=exc)
    if status in (500, 502, 503):
        return GoogleWorkspaceError(
            message="Google API server error",
            error_code="PROVIDER_ERROR",
            retryable=True,
            original_error=exc,
        )

    error_str = blob.lower()
    if _is_auth_blob(blob):
        return DriveAuthError(
            message=(
                "Google Drive token expired or invalid. "
                "Reconnect Google Drive under Studio Account → Integrations, then retry."
            ),
            original_error=exc,
        )
    if "403" in error_str or "permission" in error_str or "forbidden" in error_str:
        return DrivePermissionError(message="Permission denied", original_error=exc)
    if "404" in error_str or "not found" in error_str:
        return DriveNotFoundError(message="Resource not found", original_error=exc)
    if "429" in error_str or "rate" in error_str or "quota" in error_str:
        return DriveRateLimitError(message="Rate limit exceeded", original_error=exc)
    if "500" in error_str or "502" in error_str or "503" in error_str:
        return GoogleWorkspaceError(
            message="Google API server error",
            error_code="PROVIDER_ERROR",
            retryable=True,
            original_error=exc,
        )
    return GoogleWorkspaceError(
        message=str(exc),
        error_code="UNKNOWN_ERROR",
        retryable=False,
        original_error=exc,
    )
