"""
Load OAuth credentials from per-invocation tool inputs.

Credentials are never read from the environment for tool calls.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuth2Credentials

from app.auth.scopes import SCOPES
from app.core.exceptions import DriveAuthError, GoogleWorkspaceError

_RECONNECT_HINT = (
    "Reconnect Google Drive under Studio Account → Integrations "
    "(Disconnect, then Connect), then retry the catalog run."
)


def _is_oauth_creds(creds_dict: dict) -> bool:
    """Check if credentials dict is OAuth (user) format."""
    return (
        creds_dict.get("type") == "oauth"
        or (creds_dict.get("refresh_token") and creds_dict.get("client_id"))
        or (creds_dict.get("refresh_token") and "client_secret" in creds_dict)
    )


def _parse_expiry(creds_dict: dict) -> Optional[datetime]:
    """Parse vault/Google expiry as naive UTC datetime (google-auth convention)."""
    raw = creds_dict.get("expiry") or creds_dict.get("expires_at") or creds_dict.get("token_expiry")
    if isinstance(raw, (int, float)) and raw > 0:
        return datetime.fromtimestamp(float(raw), tz=timezone.utc).replace(tzinfo=None)
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    expires_in = creds_dict.get("expires_in")
    if isinstance(expires_in, int) and expires_in > 0:
        return datetime.utcnow() + timedelta(seconds=expires_in)
    return None


def _refresh_oauth_credentials(creds: OAuth2Credentials) -> OAuth2Credentials:
    if not creds.refresh_token or not creds.client_id or not creds.client_secret:
        raise DriveAuthError(
            "Google Drive access token expired and cannot be refreshed "
            f"(missing refresh_token or OAuth client). {_RECONNECT_HINT}",
        )
    try:
        creds.refresh(Request())
    except RefreshError as exc:
        raise DriveAuthError(
            f"Google Drive token expired or was revoked. {_RECONNECT_HINT}",
            original_error=exc,
        ) from exc
    except Exception as exc:
        raise DriveAuthError(
            f"Google Drive token refresh failed. {_RECONNECT_HINT}",
            original_error=exc,
        ) from exc
    return creds


def get_credentials(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> OAuth2Credentials:
    """
    Load OAuth credentials from input parameters.
    Requires one of: credentials_path or credentials_json.
    Both must contain OAuth token JSON (from Connect with Google or oauth_connect.py).

    Vault inject historically omitted expiry. google-auth then treats the access
    token as valid forever and Google returns 401 after ~1 hour. Refresh when
    expiry is missing or the access token is expired.
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

    expiry = _parse_expiry(creds_dict)
    creds = OAuth2Credentials(
        token=creds_dict.get("token") or creds_dict.get("access_token"),
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=creds_dict.get("scopes", SCOPES),
        expiry=expiry,
    )
    if expiry is None or creds.expired:
        _refresh_oauth_credentials(creds)
    return creds
