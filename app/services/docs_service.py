"""
Google Docs API wrapper.

Agent-friendly helpers hide raw Docs index arithmetic where possible.
"""

from typing import Optional, Tuple

from googleapiclient.errors import HttpError

from app.auth.clients import build_docs_service
from app.core.exceptions import GoogleWorkspaceError, normalize_google_error
from app.services.drive_service import DriveService

EXPORT_MIME_MAP = {
    "text/plain": "text/plain",
    "application/pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
}

MAX_EXPORT_BYTES = 25 * 1024 * 1024


class DocsService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._credentials_path = credentials_path
        self._credentials_json = credentials_json
        self._docs = build_docs_service(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )
        self._drive = DriveService(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    def create_document(
        self,
        title: str = "Untitled document",
        parent_folder_id: Optional[str] = None,
    ) -> dict:
        try:
            doc = self._docs.documents().create(body={"title": title}).execute()
        except HttpError as e:
            raise normalize_google_error(e)
        document_id = doc["documentId"]
        parent_applied, parent_error = self._drive.apply_parent(
            document_id, parent_folder_id
        )
        web_view_link = None
        try:
            meta = self._drive.get_metadata(document_id)
            web_view_link = meta.web_view_link
        except GoogleWorkspaceError:
            # Create already succeeded — keep resource id (ADR-0004)
            pass
        return {
            "document_id": document_id,
            "title": doc.get("title", title),
            "web_view_link": web_view_link,
            "parent_applied": parent_applied,
            "parent_error": parent_error,
        }

    def read_document(self, document_id: str) -> dict:
        try:
            doc = self._docs.documents().get(documentId=document_id).execute()
            text = self._extract_text(doc)
            return {
                "document_id": document_id,
                "title": doc.get("title"),
                "text": text,
                "revision_id": doc.get("revisionId"),
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def append_text(self, document_id: str, text: str) -> None:
        if not text:
            raise GoogleWorkspaceError(
                "text must not be empty",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            doc = self._docs.documents().get(documentId=document_id).execute()
            end_index = self._body_end_index(doc)
            # Insert before the final newline of the body
            insert_at = max(1, end_index - 1)
            requests = [
                {
                    "insertText": {
                        "location": {"index": insert_at},
                        "text": text if text.endswith("\n") else text + "\n",
                    }
                }
            ]
            self._docs.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()
        except HttpError as e:
            raise normalize_google_error(e)

    def replace_text(
        self,
        document_id: str,
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
                self._docs.documents()
                .batchUpdate(
                    documentId=document_id,
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

    def insert_text(
        self,
        document_id: str,
        text: str,
        index: Optional[int] = None,
    ) -> None:
        if not text:
            raise GoogleWorkspaceError(
                "text must not be empty",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            if index is None:
                self.append_text(document_id, text)
                return
            if index < 1:
                raise GoogleWorkspaceError(
                    "index must be >= 1 (Docs body starts at index 1)",
                    error_code="VALIDATION_ERROR",
                    retryable=False,
                )
            self._docs.documents().batchUpdate(
                documentId=document_id,
                body={
                    "requests": [
                        {"insertText": {"location": {"index": index}, "text": text}}
                    ]
                },
            ).execute()
        except HttpError as e:
            raise normalize_google_error(e)

    def export_document(
        self, document_id: str, export_format: str = "text/plain"
    ) -> Tuple[bytes, str]:
        mime = EXPORT_MIME_MAP.get(export_format)
        if not mime:
            raise GoogleWorkspaceError(
                f"Unsupported export_format: {export_format}. "
                f"Supported: {', '.join(sorted(EXPORT_MIME_MAP.keys()))}",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        content = self._drive.export_file(document_id, mime)
        if len(content) > MAX_EXPORT_BYTES:
            raise GoogleWorkspaceError(
                f"Export exceeds {MAX_EXPORT_BYTES} bytes limit",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        return content, mime

    @staticmethod
    def _extract_text(doc: dict) -> str:
        parts = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for pe in paragraph.get("elements", []):
                text_run = pe.get("textRun")
                if text_run and "content" in text_run:
                    parts.append(text_run["content"])
        return "".join(parts)

    @staticmethod
    def _body_end_index(doc: dict) -> int:
        content = doc.get("body", {}).get("content", [])
        if not content:
            return 1
        return content[-1].get("endIndex", 1)
