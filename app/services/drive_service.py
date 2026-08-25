"""
Google Drive API wrapper layer.

Abstractions for Drive operations. Credentials are passed as input parameters
(credentials_path or credentials_json) by the caller - not read from environment.
"""

import base64
import io
import os
from typing import List, Optional, Tuple

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from app.auth.clients import build_drive_service
from app.core.exceptions import DriveError, GoogleWorkspaceError, normalize_google_error
from app.schemas.drive import FileMetadata

# Re-export for scripts that historically imported SCOPES from here
from app.auth.scopes import SCOPES  # noqa: F401

_DRIVE_QUERY_MARKERS = (
    "contains",
    "mimetype",
    "in parents",
    "trashed",
    "fulltext",
    "modifiedtime",
    "createdtime",
    "starred",
    "sharedwithme",
    "name =",
    "name=",
)


def coerce_drive_list_query(query: Optional[str]) -> Optional[str]:
    """Turn free-text (e.g. a purchase request title) into Drive `q` syntax."""
    if query is None:
        return None
    text = str(query).strip()
    if not text:
        return None
    lower = text.lower()
    if any(marker in lower for marker in _DRIVE_QUERY_MARKERS):
        return text
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return f"name contains '{escaped}'"


class DriveService:
    """
    Google Drive API wrapper.
    Stateless - each operation is independent.
    Credentials are passed at construction.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._service = build_drive_service(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    @property
    def service(self):
        return self._service

    def _file_to_metadata(self, f: dict) -> FileMetadata:
        """Convert Drive API file dict to FileMetadata."""
        mime = f.get("mimeType", "")
        return FileMetadata(
            id=f["id"],
            name=f.get("name", ""),
            mime_type=mime,
            size=int(f["size"]) if f.get("size") else None,
            created_time=f.get("createdTime"),
            modified_time=f.get("modifiedTime"),
            parents=f.get("parents", []) or [],
            web_view_link=f.get("webViewLink"),
            is_folder=mime == "application/vnd.google-apps.folder",
            trashed=bool(f.get("trashed")),
        )

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
        query: Optional[str] = None,
        include_root_parent: bool = True,
    ) -> Tuple[List[FileMetadata], Optional[str]]:
        """
        List files in a folder or root.
        Returns (files, next_page_token).
        """
        try:
            q_parts = []
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            elif include_root_parent:
                q_parts.append("'root' in parents")
            if query:
                coerced = coerce_drive_list_query(query)
                if coerced:
                    q_parts.append(coerced)
            # Drive files.get still returns Trash by id; list must not surface deleted workbooks.
            if not query or "trashed" not in query.lower():
                q_parts.append("trashed = false")
            q_str = " and ".join(q_parts) if q_parts else "trashed = false"

            result = (
                self.service.files()
                .list(
                    q=q_str,
                    pageSize=page_size,
                    pageToken=page_token or "",
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink, trashed)",
                )
                .execute()
            )

            files = [self._file_to_metadata(f) for f in result.get("files", [])]
            next_token = result.get("nextPageToken")
            return files, next_token
        except HttpError as e:
            raise normalize_google_error(e)

    def upload_file(
        self,
        file_name: str,
        content_base64: Optional[str] = None,
        file_path: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> dict:
        """
        Upload a file. Provide either content_base64 or file_path.
        Returns file dict with id, name, webViewLink.
        """
        if not content_base64 and not file_path:
            raise DriveError("Either content_base64 or file_path must be provided")

        try:
            body = {"name": file_name}
            if parent_folder_id:
                body["parents"] = [parent_folder_id]

            if content_base64:
                content_bytes = base64.b64decode(content_base64)
                media = MediaIoBaseUpload(
                    io.BytesIO(content_bytes),
                    mimetype=mime_type or "application/octet-stream",
                    resumable=True,
                )
            else:
                if not os.path.exists(file_path):
                    raise DriveError(f"File not found: {file_path}")
                media = MediaFileUpload(
                    file_path,
                    mimetype=mime_type,
                    resumable=True,
                )

            file = (
                self.service.files()
                .create(body=body, media_body=media, fields="id, name, webViewLink")
                .execute()
            )
            return file
        except HttpError as e:
            raise normalize_google_error(e)

    def update_file_content(
        self,
        file_id: str,
        content_bytes: bytes,
        mime_type: str = "application/octet-stream",
    ) -> dict:
        """Overwrite file media content. Returns updated file metadata."""
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(content_bytes),
                mimetype=mime_type,
                resumable=True,
            )
            return (
                self.service.files()
                .update(fileId=file_id, media_body=media, fields="id, name, webViewLink, mimeType")
                .execute()
            )
        except HttpError as e:
            raise normalize_google_error(e)

    def download_file(self, file_id: str) -> Tuple[bytes, str, str]:
        """
        Download file content. Returns (content_bytes, mime_type, file_name).
        """
        try:
            meta = (
                self.service.files()
                .get(fileId=file_id, fields="name, mimeType")
                .execute()
            )
            name = meta.get("name", "unknown")
            mime = meta.get("mimeType", "application/octet-stream")

            export_mimes = {
                "application/vnd.google-apps.document": "application/pdf",
                "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.google-apps.presentation": "application/pdf",
            }
            if mime in export_mimes:
                content = (
                    self.service.files()
                    .export_media(fileId=file_id, mimeType=export_mimes[mime])
                    .execute()
                )
            else:
                content = (
                    self.service.files()
                    .get_media(fileId=file_id)
                    .execute()
                )
            return content, mime, name
        except HttpError as e:
            raise normalize_google_error(e)

    def export_file(self, file_id: str, export_mime_type: str) -> bytes:
        """Export a Google Workspace file to the given MIME type."""
        try:
            return (
                self.service.files()
                .export_media(fileId=file_id, mimeType=export_mime_type)
                .execute()
            )
        except HttpError as e:
            raise normalize_google_error(e)

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
    ) -> dict:
        """Create a folder. Returns folder dict with id, name, webViewLink."""
        try:
            body = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_folder_id:
                body["parents"] = [parent_folder_id]

            folder = (
                self.service.files()
                .create(body=body, fields="id, name, webViewLink")
                .execute()
            )
            return folder
        except HttpError as e:
            raise normalize_google_error(e)

    def move_file(self, file_id: str, new_parent_folder_id: str) -> dict:
        """Move file to a new parent folder. Returns updated file dict."""
        try:
            file = (
                self.service.files()
                .get(fileId=file_id, fields="parents")
                .execute()
            )
            prev_parents = ",".join(file.get("parents", []))

            file = (
                self.service.files()
                .update(
                    fileId=file_id,
                    addParents=new_parent_folder_id,
                    removeParents=prev_parents,
                    fields="id, parents",
                )
                .execute()
            )
            return file
        except HttpError as e:
            raise normalize_google_error(e)

    def apply_parent(
        self, file_id: str, parent_folder_id: Optional[str]
    ) -> Tuple[bool, Optional[dict]]:
        """
        Move file into parent_folder_id when provided (soft-fail).

        Returns (parent_applied, parent_error):
        - (False, None) when no parent was requested
        - (True, None) when move succeeded
        - (False, error_dict) when move failed after create — callers keep the
          resource id so agents can recover via move_file (ADR-0004)
        """
        if not parent_folder_id:
            return False, None
        try:
            self.move_file(file_id=file_id, new_parent_folder_id=parent_folder_id)
            return True, None
        except GoogleWorkspaceError as e:
            return False, e.to_dict()

    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file (bypasses trash)."""
        try:
            self.service.files().delete(fileId=file_id).execute()
        except HttpError as e:
            raise normalize_google_error(e)

    def get_metadata(self, file_id: str) -> FileMetadata:
        """Get file metadata by ID."""
        try:
            file = (
                self.service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink, trashed",
                )
                .execute()
            )
            return self._file_to_metadata(file)
        except HttpError as e:
            raise normalize_google_error(e)
