"""Google Forms MCP tools."""

import logging
from typing import List, Optional

from pydantic import Field

from app.schemas.forms import (
    AddFormQuestionResponse,
    CreateFormResponse,
    FormQuestionSummary,
    FormResponseSummary,
    GetFormResponseDetailResponse,
    GetFormResponseModel,
    ListFormResponsesResponse,
    UpdateFormInfoResponse,
)
from app.tools.common import (
    CREDENTIALS_REQUIRED_ERROR,
    DriveError,
    credentials_missing,
    error_dict,
    get_forms,
)

logger = logging.getLogger(__name__)


def register(mcp) -> None:
    @mcp.tool()
    def create_form(
        title: str = Field(default="Untitled form", description="Form title"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
        parent_folder_id: Optional[str] = Field(default=None, description="Optional Drive parent folder ID"),
    ) -> CreateFormResponse:
        """Create a Google Form."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return CreateFormResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_forms(credentials_path, credentials_json).create_form(
                title=title, parent_folder_id=parent_folder_id
            )
            return CreateFormResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"create_form failed: {e.message}")
            return CreateFormResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def get_form(
        form_id: str = Field(..., description="Form ID"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> GetFormResponseModel:
        """Read form structure (title, description, questions)."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return GetFormResponseModel(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_forms(credentials_path, credentials_json).get_form(form_id)
            return GetFormResponseModel(
                success=True,
                form_id=result["form_id"],
                title=result.get("title"),
                description=result.get("description"),
                responder_uri=result.get("responder_uri"),
                questions=[FormQuestionSummary(**q) for q in result.get("questions", [])],
            )
        except DriveError as e:
            logger.error(f"get_form failed: {e.message}")
            return GetFormResponseModel(success=False, error=error_dict(e))

    @mcp.tool()
    def update_form_info(
        form_id: str = Field(..., description="Form ID"),
        title: Optional[str] = Field(default=None, description="New form title"),
        description: Optional[str] = Field(default=None, description="New form description"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> UpdateFormInfoResponse:
        """Update form title and/or description."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return UpdateFormInfoResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            get_forms(credentials_path, credentials_json).update_info(
                form_id, title=title, description=description
            )
            return UpdateFormInfoResponse(
                success=True, form_id=form_id, message="Form info updated"
            )
        except DriveError as e:
            logger.error(f"update_form_info failed: {e.message}")
            return UpdateFormInfoResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def add_form_question(
        form_id: str = Field(..., description="Form ID"),
        title: str = Field(..., description="Question title/prompt"),
        question_type: str = Field(
            default="short_answer",
            description="short_answer | paragraph | multiple_choice | checkbox",
        ),
        options: Optional[List[str]] = Field(
            default=None, description="Required for multiple_choice and checkbox"
        ),
        required: bool = Field(default=False, description="Whether the question is required"),
        index: int = Field(default=0, description="Insertion index in the form"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> AddFormQuestionResponse:
        """Add a question to a Google Form."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return AddFormQuestionResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_forms(credentials_path, credentials_json).add_question(
                form_id,
                title=title,
                question_type=question_type,
                options=options,
                required=required,
                index=index,
            )
            return AddFormQuestionResponse(success=True, form_id=form_id, **result)
        except DriveError as e:
            logger.error(f"add_form_question failed: {e.message}")
            return AddFormQuestionResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def list_form_responses(
        form_id: str = Field(..., description="Form ID"),
        page_size: int = Field(default=50, description="Max responses per page"),
        page_token: Optional[str] = Field(default=None, description="Pagination token"),
        include_answers: bool = Field(
            default=False,
            description="Opt-in to include answer payloads (may contain PII; default false)",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ListFormResponsesResponse:
        """List form responses (read-only). Set include_answers=true only when answer payloads are required."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ListFormResponsesResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_forms(credentials_path, credentials_json).list_responses(
                form_id,
                page_size=page_size,
                page_token=page_token,
                include_answers=include_answers,
            )
            return ListFormResponsesResponse(
                success=True,
                form_id=form_id,
                responses=[FormResponseSummary(**r) for r in result.get("responses", [])],
                next_page_token=result.get("next_page_token"),
            )
        except DriveError as e:
            logger.error(f"list_form_responses failed: {e.message}")
            return ListFormResponsesResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def get_form_response(
        form_id: str = Field(..., description="Form ID"),
        response_id: str = Field(..., description="Response ID"),
        include_answers: bool = Field(
            default=False,
            description="Opt-in to include answer payloads (may contain PII; default false)",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> GetFormResponseDetailResponse:
        """Get a single form response by ID (read-only). Set include_answers=true to load answers."""
        try:
            if credentials_missing(credentials_path, credentials_json):
                return GetFormResponseDetailResponse(
                    success=False, error=CREDENTIALS_REQUIRED_ERROR
                )
            result = get_forms(credentials_path, credentials_json).get_response(
                form_id, response_id, include_answers=include_answers
            )
            return GetFormResponseDetailResponse(
                success=True,
                form_id=form_id,
                response_id=result.get("response_id"),
                create_time=result.get("create_time"),
                last_submitted_time=result.get("last_submitted_time"),
                answers=result.get("answers"),
            )
        except DriveError as e:
            logger.error(f"get_form_response failed: {e.message}")
            return GetFormResponseDetailResponse(success=False, error=error_dict(e))
