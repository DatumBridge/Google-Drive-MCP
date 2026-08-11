from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ErrorResponse


class CreateDocumentResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    title: Optional[str] = None
    web_view_link: Optional[str] = None
    parent_applied: Optional[bool] = None
    parent_error: Optional[ErrorResponse] = None
    error: Optional[ErrorResponse] = None


class ReadDocumentResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    revision_id: Optional[str] = None
    error: Optional[ErrorResponse] = None


class AppendDocumentTextResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[ErrorResponse] = None


class ReplaceDocumentTextResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    occurrences_changed: Optional[int] = None
    message: Optional[str] = None
    error: Optional[ErrorResponse] = None


class InsertDocumentTextResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[ErrorResponse] = None


class ExportDocumentResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    mime_type: Optional[str] = None
    content_base64: Optional[str] = None
    content_text: Optional[str] = None
    error: Optional[ErrorResponse] = None
