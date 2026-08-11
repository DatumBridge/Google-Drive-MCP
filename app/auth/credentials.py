"""
Load OAuth credentials from per-invocation tool inputs.

Credentials are never read from the environment for tool calls.
"""

import json
import os
from typing import Optional

from google.oauth2.credentials import Credentials as OAuth2Credentials

from app.auth.scopes import SCOPES
from app.core.exceptions import GoogleWorkspaceError


def _is_oauth_creds(creds_dict: dict) -> bool:
    """Check if credentials dict is OAuth (user) format."""
    return (
        creds_dict.get("type") == "oauth"
        or (creds_dict.get("refresh_token") and creds_dict.get("client_id"))
        or (creds_dict.get("refresh_token") and "client_secret" in creds_dict)
    )


def get_credentials(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> OAuth2Credentials:
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
        raise GoogleWorkspaceError(
            "Credentials required: provide credentials_path or credentials_json (OAuth token)",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )

    if not _is_oauth_creds(creds_dict):
        raise GoogleWorkspaceError(
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
