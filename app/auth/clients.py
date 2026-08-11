"""
Build Google API discovery clients from OAuth credentials.
"""

from typing import Any, Optional

from googleapiclient.discovery import build

from app.auth.credentials import get_credentials


def build_drive_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> Any:
    creds = get_credentials(credentials_path=credentials_path, credentials_json=credentials_json)
    return build("drive", "v3", credentials=creds)


def build_docs_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> Any:
    creds = get_credentials(credentials_path=credentials_path, credentials_json=credentials_json)
    return build("docs", "v1", credentials=creds)


def build_sheets_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> Any:
    creds = get_credentials(credentials_path=credentials_path, credentials_json=credentials_json)
    return build("sheets", "v4", credentials=creds)


def build_slides_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> Any:
    creds = get_credentials(credentials_path=credentials_path, credentials_json=credentials_json)
    return build("slides", "v1", credentials=creds)


def build_forms_service(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> Any:
    creds = get_credentials(credentials_path=credentials_path, credentials_json=credentials_json)
    return build("forms", "v1", credentials=creds)
