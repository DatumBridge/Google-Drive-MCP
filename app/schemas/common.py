"""Shared schema helpers for MCP tool responses."""

from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error structure for MCP."""

    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    retryable: bool = Field(default=False, description="Whether client should retry")
    original_provider_error: Optional[str] = Field(
        default=None, description="Original Google API error"
    )


CREDENTIALS_REQUIRED_ERROR = {
    "error_code": "CREDENTIALS_REQUIRED",
    "error_message": "Provide credentials_path or credentials_json",
    "retryable": False,
    "original_provider_error": None,
}
