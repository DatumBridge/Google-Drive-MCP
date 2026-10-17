"""
Google Docs API wrapper.

Agent-friendly helpers hide raw Docs index arithmetic where possible.
"""

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

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

    def read_single_document(
        self,
        file_id: str,
        name: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> dict:
        """Read a single document/file and return text content."""
        try:
            # If name or mime_type not provided, fetch metadata
            if not mime_type or not name:
                try:
                    meta = self._drive.get_metadata(file_id)
                    name = name or meta.name
                    mime_type = mime_type or meta.mime_type
                except Exception:
                    pass

            # 1. Google Docs native format
            if mime_type == "application/vnd.google-apps.document":
                # Try Docs API first
                try:
                    doc = self._docs.documents().get(documentId=file_id).execute()
                    text = self._extract_text(doc)
                    return {
                        "document_id": file_id,
                        "name": name or doc.get("title"),
                        "title": name or doc.get("title"),
                        "mime_type": mime_type,
                        "text": text,
                        "success": True,
                        "error": None,
                    }
                except Exception:
                    # Fallback to Drive API export (works even if Docs API is disabled)
                    export_bytes = (
                        self._drive.service.files()
                        .export(fileId=file_id, mimeType="text/plain")
                        .execute()
                    )
                    text = (
                        export_bytes.decode("utf-8", errors="replace")
                        if isinstance(export_bytes, bytes)
                        else str(export_bytes)
                    )
                    return {
                        "document_id": file_id,
                        "name": name,
                        "title": name,
                        "mime_type": mime_type,
                        "text": text,
                        "success": True,
                        "error": None,
                    }

            lower_name = (name or "").lower()
            unsupported_exts = (
                ".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".bin", ".dmg", ".iso",
                ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mp3", ".avi", ".mkv",
            )
            if (
                any(lower_name.endswith(ext) for ext in unsupported_exts)
                or (
                    mime_type
                    and (
                        "zip" in mime_type
                        or "compressed" in mime_type
                        or mime_type.startswith("image/")
                        or mime_type.startswith("audio/")
                        or mime_type.startswith("video/")
                        or "application/x-msdownload" in mime_type
                        or "application/octet-stream" in mime_type
                    )
                    and not lower_name.endswith(".docx")
                    and not lower_name.endswith(".pdf")
                    and mime_type != "application/pdf"
                )
            ):
                return {
                    "document_id": file_id,
                    "name": name,
                    "title": name,
                    "mime_type": mime_type,
                    "text": None,
                    "success": False,
                    "error": f"File '{name}' ({mime_type}) is a binary file and cannot be read as text.",
                }

            # 2. Download content from Drive for other types
            content_bytes, dl_mime, dl_name = self._drive.download_file(file_id)
            name = name or dl_name
            mime_type = mime_type or dl_mime

            # PDF (.pdf)
            if (name and name.lower().endswith(".pdf")) or (mime_type == "application/pdf"):
                try:
                    import pypdf

                    reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                    pages_text = []
                    for page in reader.pages:
                        page_txt = page.extract_text() or ""
                        if page_txt.strip():
                            pages_text.append(page_txt.strip())
                    text = "\n\n".join(pages_text)
                    return {
                        "document_id": file_id,
                        "name": name,
                        "title": name,
                        "mime_type": mime_type or "application/pdf",
                        "text": text,
                        "success": True,
                        "error": None,
                    }
                except Exception as pdf_err:
                    return {
                        "document_id": file_id,
                        "name": name,
                        "title": name,
                        "mime_type": mime_type or "application/pdf",
                        "text": None,
                        "success": False,
                        "error": f"Failed to extract text from PDF: {pdf_err}",
                    }

            # Word .docx
            if (name and name.lower().endswith(".docx")) or (
                mime_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    paragraphs = []
                    for p in tree.iter(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
                    ):
                        t_nodes = [
                            node.text
                            for node in p.iter(
                                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
                            )
                            if node.text
                        ]
                        if t_nodes:
                            paragraphs.append("".join(t_nodes))
                    text = "\n".join(paragraphs)
                    return {
                        "document_id": file_id,
                        "name": name,
                        "title": name,
                        "mime_type": mime_type,
                        "text": text,
                        "success": True,
                        "error": None,
                    }

            # Text / XML / JSON / CSV / MD / Code
            if (
                (
                    mime_type
                    and (
                        mime_type.startswith("text/")
                        or "xml" in mime_type
                        or "json" in mime_type
                        or "csv" in mime_type
                        or "yaml" in mime_type
                    )
                )
                or (
                    name
                    and any(
                        name.lower().endswith(ext)
                        for ext in [
                            ".txt",
                            ".xml",
                            ".json",
                            ".csv",
                            ".tsv",
                            ".md",
                            ".yaml",
                            ".yml",
                            ".html",
                            ".htm",
                            ".log",
                        ]
                    )
                )
            ):
                text = content_bytes.decode("utf-8", errors="replace")
                return {
                    "document_id": file_id,
                    "name": name,
                    "title": name,
                    "mime_type": mime_type,
                    "text": text,
                    "success": True,
                    "error": None,
                }

            # Unsupported binary type
            return {
                "document_id": file_id,
                "name": name,
                "title": name,
                "mime_type": mime_type,
                "text": None,
                "success": False,
                "error": f"File '{name}' ({mime_type}) is not a supported text document format.",
            }

        except Exception as e:
            return {
                "document_id": file_id,
                "name": name,
                "title": name,
                "mime_type": mime_type,
                "text": None,
                "success": False,
                "error": str(e),
            }

    def read_documents(
        self,
        files: Optional[List[Any]] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Read multiple documents/files as text.
        Accepts:
          - files: list of file dicts (from list_files), or list of file IDs.
          - document_ids: list of document/file ID strings.
        """
        target_items = []
        if files:
            for item in files:
                if isinstance(item, dict):
                    f_id = item.get("id") or item.get("document_id")
                    if f_id:
                        target_items.append({
                            "id": str(f_id),
                            "name": item.get("name") or item.get("title"),
                            "mime_type": item.get("mime_type"),
                        })
                elif hasattr(item, "id"):
                    target_items.append({
                        "id": str(item.id),
                        "name": getattr(item, "name", None),
                        "mime_type": getattr(item, "mime_type", None),
                    })
                elif isinstance(item, str) and item.strip():
                    target_items.append({"id": item.strip(), "name": None, "mime_type": None})

        if document_ids:
            for doc_id in document_ids:
                if isinstance(doc_id, str) and doc_id.strip():
                    if not any(t["id"] == doc_id.strip() for t in target_items):
                        target_items.append({"id": doc_id.strip(), "name": None, "mime_type": None})

        results = []
        for item in target_items:
            res = self.read_single_document(
                file_id=item["id"],
                name=item.get("name"),
                mime_type=item.get("mime_type"),
            )
            results.append(res)
        return results

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
