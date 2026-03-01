"""Core modules: exceptions, auth, error handling."""

from .exceptions import (
    DriveError,
    DriveAuthError,
    DriveNotFoundError,
    DrivePermissionError,
    DriveRateLimitError,
)

__all__ = [
    "DriveError",
    "DriveAuthError",
    "DriveNotFoundError",
    "DrivePermissionError",
    "DriveRateLimitError",
]
