"""
Google Slides API wrapper — text-centric agent operations.
"""

from typing import List, Optional, Tuple
import json
import uuid

from googleapiclient.errors import HttpError

from app.auth.clients import build_slides_service
from app.core.exceptions import GoogleWorkspaceError, normalize_google_error
from app.services.drive_service import DriveService

EXPORT_MIME_MAP = {
    "pdf": "application/pdf",
    "application/pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
}

MAX_EXPORT_BYTES = 25 * 1024 * 1024
MAX_SLIDES = 20


def parse_slide_outline(slides, description: Optional[str] = None, title: str = "") -> List[dict]:
    """Turn planner slide payloads into title/body pairs.

    An empty list falls back to description so a successful create is not a blank deck.
    """
    items = _coerce_slides(slides)
    if items:
        return items
    body = (description or "").strip()
    if not body or body in ("[]", "null", "{}"):
        return []
    heading = (title or "Slide").strip() or "Slide"
    if body == heading:
        return []
    return [{"title": heading[:200], "body": body[:8000]}]


def _coerce_slides(slides) -> List[dict]:
    if slides is None:
        return []
    if isinstance(slides, str):
        text = slides.strip()
        if text in ("", "[]", "null", "{}"):
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [{"title": "", "body": text[:8000]}]
        return _coerce_slides(parsed)
    if isinstance(slides, dict):
        one = _one_slide(slides)
        return [one] if one["title"] or one["body"] else []
    if isinstance(slides, list):
        out = []
        for item in slides[:MAX_SLIDES]:
            if isinstance(item, str) and item.strip() and item.strip() not in ("[]", "null"):
                out.append({"title": "", "body": item.strip()[:8000]})
            elif isinstance(item, dict):
                one = _one_slide(item)
                if one["title"] or one["body"]:
                    out.append(one)
        return out
    return []


def _one_slide(item: dict) -> dict:
    heading = str(item.get("title") or item.get("heading") or "").strip()[:200]
    body = str(
        item.get("body") or item.get("text") or item.get("content") or item.get("notes") or ""
    ).strip()[:8000]
    return {"title": heading, "body": body}


class SlidesService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._slides = build_slides_service(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )
        self._drive = DriveService(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    def create_presentation(
        self,
        title: str = "Untitled presentation",
        parent_folder_id: Optional[str] = None,
        slides=None,
        description: Optional[str] = None,
    ) -> dict:
        try:
            presentation = (
                self._slides.presentations().create(body={"title": title}).execute()
            )
        except HttpError as e:
            raise normalize_google_error(e)
        presentation_id = presentation["presentationId"]
        parent_applied, parent_error = self._drive.apply_parent(
            presentation_id, parent_folder_id
        )
        presentation_url = None
        try:
            meta = self._drive.get_metadata(presentation_id)
            presentation_url = meta.web_view_link
        except GoogleWorkspaceError:
            # Create already succeeded — keep resource id (ADR-0004)
            pass
        outline = parse_slide_outline(slides, description, title)
        if outline:
            self.fill_outline(presentation_id, outline)
        return {
            "presentation_id": presentation_id,
            "title": presentation.get("title", title),
            "presentation_url": presentation_url,
            "parent_applied": parent_applied,
            "parent_error": parent_error,
            "slides_written": len(outline),
        }

    def list_slides(self, presentation_id: str) -> List[dict]:
        try:
            presentation = (
                self._slides.presentations().get(presentationId=presentation_id).execute()
            )
            slides = []
            for i, slide in enumerate(presentation.get("slides", [])):
                object_id = slide.get("objectId", "")
                title_hint = self._first_text(slide)
                slides.append(
                    {
                        "object_id": object_id,
                        "index": i,
                        "title_hint": title_hint[:120] if title_hint else None,
                    }
                )
            return slides
        except HttpError as e:
            raise normalize_google_error(e)

    def fill_outline(self, presentation_id: str, outline: List[dict]) -> None:
        existing = self.list_slides(presentation_id)
        for index, slide in enumerate(outline):
            text = "\n".join(part for part in (slide.get("title"), slide.get("body")) if part)
            if not text:
                continue
            if index == 0 and existing:
                self.insert_text(presentation_id, text, slide_object_id=existing[0]["object_id"])
                continue
            slide_id = self.add_slide(presentation_id, layout="BLANK")
            self.insert_text(presentation_id, text, slide_object_id=slide_id)

    def read_presentation(self, presentation_id: str) -> dict:
        try:
            presentation = (
                self._slides.presentations().get(presentationId=presentation_id).execute()
            )
            slides = []
            for i, slide in enumerate(presentation.get("slides", [])):
                slides.append(
                    {
                        "object_id": slide.get("objectId", ""),
                        "index": i,
                        "text": self._slide_text(slide),
                    }
                )
            return {
                "presentation_id": presentation_id,
                "title": presentation.get("title"),
                "slides": slides,
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def add_slide(
        self,
        presentation_id: str,
        layout: str = "BLANK",
        insertion_index: Optional[int] = None,
    ) -> str:
        try:
            slide_id = f"slide_{uuid.uuid4().hex[:12]}"
            create_slide = {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": layout},
            }
            if insertion_index is not None:
                create_slide["insertionIndex"] = insertion_index
            self._slides.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": [{"createSlide": create_slide}]},
            ).execute()
            return slide_id
        except HttpError as e:
            raise normalize_google_error(e)

    def insert_text(
        self,
        presentation_id: str,
        text: str,
        slide_object_id: Optional[str] = None,
        shape_object_id: Optional[str] = None,
    ) -> None:
        if not text:
            raise GoogleWorkspaceError(
                "text must not be empty",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            requests = []
            if shape_object_id:
                requests.append(
                    {
                        "insertText": {
                            "objectId": shape_object_id,
                            "insertionIndex": 0,
                            "text": text,
                        }
                    }
                )
            else:
                if not slide_object_id:
                    slides = self.list_slides(presentation_id)
                    if not slides:
                        raise GoogleWorkspaceError(
                            "Presentation has no slides",
                            error_code="VALIDATION_ERROR",
                            retryable=False,
                        )
                    slide_object_id = slides[0]["object_id"]
                box_id = f"textbox_{uuid.uuid4().hex[:12]}"
                requests.extend(
                    [
                        {
                            "createShape": {
                                "objectId": box_id,
                                "shapeType": "TEXT_BOX",
                                "elementProperties": {
                                    "pageObjectId": slide_object_id,
                                    "size": {
                                        "width": {"magnitude": 400, "unit": "PT"},
                                        "height": {"magnitude": 100, "unit": "PT"},
                                    },
                                    "transform": {
                                        "scaleX": 1,
                                        "scaleY": 1,
                                        "translateX": 50,
                                        "translateY": 50,
                                        "unit": "PT",
                                    },
                                },
                            }
                        },
                        {
                            "insertText": {
                                "objectId": box_id,
                                "insertionIndex": 0,
                                "text": text,
                            }
                        },
                    ]
                )
            self._slides.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()
        except HttpError as e:
            raise normalize_google_error(e)

    def replace_text(
        self,
        presentation_id: str,
        find_text: str,
        replace_text: str,
        match_case: bool = True,
    ) -> int:
        if not find_text:
            raise GoogleWorkspaceError(
                "find_text must not be empty",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            result = (
                self._slides.presentations()
                .batchUpdate(
                    presentationId=presentation_id,
                    body={
                        "requests": [
                            {
                                "replaceAllText": {
                                    "containsText": {
                                        "text": find_text,
                                        "matchCase": match_case,
                                    },
                                    "replaceText": replace_text,
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            replies = result.get("replies", [])
            if replies:
                return replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
            return 0
        except HttpError as e:
            raise normalize_google_error(e)

    def export_presentation(
        self, presentation_id: str, export_format: str = "pdf"
    ) -> Tuple[bytes, str]:
        mime = EXPORT_MIME_MAP.get(export_format)
        if not mime:
            raise GoogleWorkspaceError(
                f"Unsupported export_format: {export_format}. Supported: pdf, pptx",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        content = self._drive.export_file(presentation_id, mime)
        if len(content) > MAX_EXPORT_BYTES:
            raise GoogleWorkspaceError(
                f"Export exceeds {MAX_EXPORT_BYTES} bytes limit",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        return content, mime

    @staticmethod
    def _slide_text(slide: dict) -> str:
        parts = []
        for element in slide.get("pageElements", []):
            shape = element.get("shape")
            if not shape:
                continue
            text = shape.get("text")
            if not text:
                continue
            for te in text.get("textElements", []):
                run = te.get("textRun")
                if run and "content" in run:
                    parts.append(run["content"])
        return "".join(parts).strip()

    def _first_text(self, slide: dict) -> str:
        return self._slide_text(slide)
