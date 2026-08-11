"""Pydantic models for Google Forms MCP tools."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ErrorResponse


class FormQuestionSummary(BaseModel):
    question_id: Optional[str] = None
    item_id: Optional[str] = None
    title: Optional[str] = None
    question_type: Optional[str] = None


class FormResponseSummary(BaseModel):
    response_id: str
    create_time: Optional[str] = None
    last_submitted_time: Optional[str] = None
    answers: Optional[dict] = None


class CreateFormResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    title: Optional[str] = None
    responder_uri: Optional[str] = None
    parent_applied: Optional[bool] = None
    parent_error: Optional[ErrorResponse] = None
    error: Optional[ErrorResponse] = None


class GetFormResponseModel(BaseModel):
    success: bool
    form_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    responder_uri: Optional[str] = None
    questions: List[FormQuestionSummary] = Field(default_factory=list)
    error: Optional[dict] = None


class UpdateFormInfoResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[dict] = None


class AddFormQuestionResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    item_id: Optional[str] = None
    question_id: Optional[str] = None
    error: Optional[dict] = None


class ListFormResponsesResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    responses: List[FormResponseSummary] = Field(default_factory=list)
    next_page_token: Optional[str] = None
    error: Optional[dict] = None


class GetFormResponseDetailResponse(BaseModel):
    success: bool
    form_id: Optional[str] = None
    response_id: Optional[str] = None
    create_time: Optional[str] = None
    last_submitted_time: Optional[str] = None
    answers: Optional[dict] = None
    error: Optional[dict] = None
