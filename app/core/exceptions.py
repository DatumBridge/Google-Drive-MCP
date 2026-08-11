"""
Error handling for Google Workspace MCP Server.

Normalizes Google API errors into MCP-compatible format:
- error_code
- error_message
- retryable (true/false)
- original_provider_error
"""

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

    def __init__(self, message: str = "Token expired or invalid", original_error: Optional[Any] = None):
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


def normalize_google_error(exc: Exception) -> GoogleWorkspaceError:
    """
    Map Google API HTTP errors to standardized GoogleWorkspaceError subclasses.
    Prefer HttpError.resp.status when available; fall back to message parsing.
    """
    status = None
    resp = getattr(exc, "resp", None)
    if resp is not None:
        status = getattr(resp, "status", None)
        if status is not None:
            try:
                status = int(status)
            except (TypeError, ValueError):
                status = None

    if status == 401:
        return DriveAuthError(message="Token expired or invalid", original_error=exc)
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

    error_str = str(exc).lower()
    if "401" in error_str or ("invalid" in error_str and "token" in error_str):
        return DriveAuthError(message="Token expired or invalid", original_error=exc)
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
