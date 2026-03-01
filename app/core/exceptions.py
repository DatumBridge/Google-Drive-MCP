"""
Error handling for Google Drive MCP Server.

Normalizes Google API errors into MCP-compatible format per design spec:
- error_code
- error_message
- retryable (true/false)
- original_provider_error
"""

from typing import Optional, Any


class DriveError(Exception):
    """Base error for Google Drive operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "DRIVE_ERROR",
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


class DriveAuthError(DriveError):
    """Authentication/authorization failure (401)."""

    def __init__(self, message: str = "Token expired or invalid", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            retryable=True,
            original_error=original_error,
        )


class DriveNotFoundError(DriveError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            retryable=False,
            original_error=original_error,
        )


class DrivePermissionError(DriveError):
    """Permission denied (403)."""

    def __init__(self, message: str = "Permission denied", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            retryable=False,
            original_error=original_error,
        )


class DriveRateLimitError(DriveError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded", original_error: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            retryable=True,
            original_error=original_error,
        )


def normalize_google_error(exc: Exception) -> DriveError:
    """
    Map Google API HTTP errors to standardized DriveError subclasses.
    """
    error_str = str(exc).lower()
    if "401" in error_str or "invalid" in error_str and "token" in error_str:
        return DriveAuthError(message="Token expired or invalid", original_error=exc)
    if "403" in error_str or "permission" in error_str or "forbidden" in error_str:
        return DrivePermissionError(message="Permission denied", original_error=exc)
    if "404" in error_str or "not found" in error_str:
        return DriveNotFoundError(message="Resource not found", original_error=exc)
    if "429" in error_str or "rate" in error_str or "quota" in error_str:
        return DriveRateLimitError(message="Rate limit exceeded", original_error=exc)
    if "500" in error_str or "502" in error_str or "503" in error_str:
        return DriveError(
            message="Google API server error",
            error_code="PROVIDER_ERROR",
            retryable=True,
            original_error=exc,
        )
    return DriveError(
        message=str(exc),
        error_code="UNKNOWN_ERROR",
        retryable=False,
        original_error=exc,
    )
