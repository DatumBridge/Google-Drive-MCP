"""Pydantic models for Google Slides MCP tools."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ErrorResponse


class SlideInfo(BaseModel):
    object_id: str
    index: int = 0
    title_hint: Optional[str] = None


class SlideTextContent(BaseModel):
    object_id: str
    index: int = 0
    text: str = ""


class CreatePresentationResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    title: Optional[str] = None
    presentation_url: Optional[str] = None
    parent_applied: Optional[bool] = None
    parent_error: Optional[ErrorResponse] = None
    slides_written: int = 0
    error: Optional[ErrorResponse] = None


class ListSlidesResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    slides: List[SlideInfo] = Field(default_factory=list)
    error: Optional[dict] = None


class ReadPresentationResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    title: Optional[str] = None
    slides: List[SlideTextContent] = Field(default_factory=list)
    error: Optional[dict] = None


class AddSlideResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    slide_object_id: Optional[str] = None
    error: Optional[dict] = None


class InsertSlideTextResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[dict] = None


class ReplacePresentationTextResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    occurrences_changed: Optional[int] = None
    message: Optional[str] = None
    error: Optional[dict] = None


class ExportPresentationResponse(BaseModel):
    success: bool
    presentation_id: Optional[str] = None
    mime_type: Optional[str] = None
    content_base64: Optional[str] = None
    error: Optional[dict] = None
