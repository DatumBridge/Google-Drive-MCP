"""
Google Drive API wrapper layer.

Abstractions for Drive operations. All Google API logic lives here per design spec.
Credentials are passed as input parameters (credentials_path or credentials_json)
by the caller - not read from environment.

Uses OAuth 2.0 for Personal Google Drive. Use "Connect with Google" in the test UI
or run scripts/oauth_connect.py to obtain an OAuth token.
"""

import json
import os
import io
import base64
from typing import Optional, List, Tuple
from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

from app.core.exceptions import normalize_google_error, DriveError
from app.schemas.mcp_models import FileMetadata

# Drive API scope - full drive access
SCOPES = ["https://www.googleapis.com/auth/drive"]


def _is_oauth_creds(creds_dict: dict) -> bool:
    """Check if credentials dict is OAuth (user) format."""
    return (
        creds_dict.get("type") == "oauth"
        or (creds_dict.get("refresh_token") and creds_dict.get("client_id"))
        or (creds_dict.get("refresh_token") and "client_secret" in creds_dict)
    )


def _get_credentials(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
):
    """
    Load OAuth credentials from input parameters.
    Requires one of: credentials_path or credentials_json.
    Both must contain OAuth token JSON (from Connect with Google or oauth_connect.py).
    """
    creds_dict = None
    if credentials_json:
        creds_dict = json.loads(credentials_json)
    elif credentials_path and os.path.exists(credentials_path):
        with open(credentials_path) as f:
            creds_dict = json.load(f)

    if not creds_dict:
        raise DriveError(
            "Credentials required: provide credentials_path or credentials_json (OAuth token)",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )

    if not _is_oauth_creds(creds_dict):
        raise DriveError(
            "OAuth credentials required. Use Connect with Google in the test UI or run scripts/oauth_connect.py to get a token.",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )

    return OAuth2Credentials(
        token=creds_dict.get("token") or creds_dict.get("access_token"),
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=creds_dict.get("scopes", SCOPES),
    )


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
        creds = _get_credentials(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )
        self._service = build("drive", "v3", credentials=creds)

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
        )

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Tuple[List[FileMetadata], Optional[str]]:
        """
        List files in a folder or root.
        Returns (files, next_page_token).
        """
        try:
            q_parts = []
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            else:
                q_parts.append("'root' in parents")
            if query:
                q_parts.append(query)
            q_str = " and ".join(q_parts) if q_parts else None

            result = (
                self.service.files()
                .list(
                    q=q_str,
                    pageSize=page_size,
                    pageToken=page_token or "",
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
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

            # Google Workspace files (Docs, Sheets, etc.) need export
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
            # Get current parents
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
                    fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink",
                )
                .execute()
            )
            return self._file_to_metadata(file)
        except HttpError as e:
            raise normalize_google_error(e)
