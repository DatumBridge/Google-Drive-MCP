"""Google Slides MCP tools."""

import base64
import logging
from typing import Optional

from pydantic import Field

from app.schemas.slides import (
    AddSlideResponse,
    CreatePresentationResponse,
    ExportPresentationResponse,
    InsertSlideTextResponse,
    ListSlidesResponse,
    ReadPresentationResponse,
    ReplacePresentationTextResponse,
    SlideInfo,
    SlideTextContent,
)
from app.tools.common import (
    CREDENTIALS_REQUIRED_ERROR,
    DriveError,
    credentials_missing,
    error_dict,
    get_slides,
)

logger = logging.getLogger(__name__)


def register(mcp) -> None:
    @mcp.tool()
    def create_presentation(
        title: str = Field(default="Untitled presentation", description="Presentation title"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
        parent_folder_id: Optional[str] = Field(default=None, description="Optional Drive parent folder ID"),
        slides: Optional[str] = Field(
            default=None,
            description="Slide content as a JSON array of {title, body}. Plain text is written as one slide. Do not pass [].",
            json_schema_extra={"x-datumbridge-encoding": "plain"},
        ),
        description: Optional[str] = Field(
            default=None,
            description="Body of the first slide when slides is empty. Used so the deck is not created blank.",
            json_schema_extra={"x-datumbridge-encoding": "plain"},
        ),
    ) -> CreatePresentationResponse:
        """Create a Google Slides presentation.

        Capabilities: drive.create_presentation
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return CreatePresentationResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_slides(credentials_path, credentials_json).create_presentation(
                title=title,
                parent_folder_id=parent_folder_id,
                slides=slides,
                description=description,
            )
            return CreatePresentationResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"create_presentation failed: {e.message}")
            return CreatePresentationResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def list_slides(
        presentation_id: str = Field(..., description="Presentation ID"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ListSlidesResponse:
        """List slides in a presentation (object IDs + text hints).

        Capabilities: drive.list_slides
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ListSlidesResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            slides = get_slides(credentials_path, credentials_json).list_slides(presentation_id)
            return ListSlidesResponse(
                success=True,
                presentation_id=presentation_id,
                slides=[SlideInfo(**s) for s in slides],
            )
        except DriveError as e:
            logger.error(f"list_slides failed: {e.message}")
            return ListSlidesResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def read_presentation(
        presentation_id: str = Field(..., description="Presentation ID"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReadPresentationResponse:
        """Extract text content per slide for agent-friendly reading.

        Capabilities: drive.read_presentation
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReadPresentationResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_slides(credentials_path, credentials_json).read_presentation(
                presentation_id
            )
            return ReadPresentationResponse(
                success=True,
                presentation_id=result["presentation_id"],
                title=result.get("title"),
                slides=[SlideTextContent(**s) for s in result.get("slides", [])],
            )
        except DriveError as e:
            logger.error(f"read_presentation failed: {e.message}")
            return ReadPresentationResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def add_slide(
        presentation_id: str = Field(..., description="Presentation ID"),
        layout: str = Field(
            default="BLANK",
            description="Predefined layout (e.g. BLANK, TITLE, TITLE_AND_BODY)",
        ),
        insertion_index: Optional[int] = Field(
            default=None, description="Optional index at which to insert the slide"
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> AddSlideResponse:
        """Add a slide to a presentation.

        Capabilities: drive.add_slide
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return AddSlideResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            slide_id = get_slides(credentials_path, credentials_json).add_slide(
                presentation_id, layout=layout, insertion_index=insertion_index
            )
            return AddSlideResponse(
                success=True, presentation_id=presentation_id, slide_object_id=slide_id
            )
        except DriveError as e:
            logger.error(f"add_slide failed: {e.message}")
            return AddSlideResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def insert_slide_text(
        presentation_id: str = Field(..., description="Presentation ID"),
        text: str = Field(..., description="Text to insert", json_schema_extra={"x-datumbridge-encoding": "plain"}),
        slide_object_id: Optional[str] = Field(
            default=None, description="Target slide object ID (defaults to first slide)"
        ),
        shape_object_id: Optional[str] = Field(
            default=None, description="Existing shape object ID to insert into"
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> InsertSlideTextResponse:
        """Insert text into a shape, or create a text box on a slide.

        Capabilities: drive.insert_slide_text
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return InsertSlideTextResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            get_slides(credentials_path, credentials_json).insert_text(
                presentation_id,
                text,
                slide_object_id=slide_object_id,
                shape_object_id=shape_object_id,
            )
            return InsertSlideTextResponse(
                success=True, presentation_id=presentation_id, message="Text inserted"
            )
        except DriveError as e:
            logger.error(f"insert_slide_text failed: {e.message}")
            return InsertSlideTextResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def replace_presentation_text(
        presentation_id: str = Field(..., description="Presentation ID"),
        find_text: str = Field(..., description="Text to find", json_schema_extra={"x-datumbridge-encoding": "plain"}),
        replace_text: str = Field(..., description="Replacement text", json_schema_extra={"x-datumbridge-encoding": "plain"}),
        match_case: bool = Field(default=True, description="Case-sensitive match"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReplacePresentationTextResponse:
        """Find and replace text across an entire presentation.

        Capabilities: drive.replace_presentation_text
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReplacePresentationTextResponse(
                    success=False, error=CREDENTIALS_REQUIRED_ERROR
                )
            count = get_slides(credentials_path, credentials_json).replace_text(
                presentation_id, find_text, replace_text, match_case=match_case
            )
            return ReplacePresentationTextResponse(
                success=True,
                presentation_id=presentation_id,
                occurrences_changed=count,
                message=f"Replaced {count} occurrence(s)",
            )
        except DriveError as e:
            logger.error(f"replace_presentation_text failed: {e.message}")
            return ReplacePresentationTextResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def export_presentation(
        presentation_id: str = Field(..., description="Presentation ID"),
        export_format: str = Field(default="pdf", description="Export format: pdf or pptx"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ExportPresentationResponse:
        """Export a presentation via Drive export (pdf/pptx).

        Capabilities: drive.export_presentation
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ExportPresentationResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            content, mime = get_slides(credentials_path, credentials_json).export_presentation(
                presentation_id, export_format
            )
            return ExportPresentationResponse(
                success=True,
                presentation_id=presentation_id,
                mime_type=mime,
                content_base64=base64.b64encode(content).decode("ascii"),
            )
        except DriveError as e:
            logger.error(f"export_presentation failed: {e.message}")
            return ExportPresentationResponse(success=False, error=error_dict(e))
