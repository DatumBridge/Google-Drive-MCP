"""
OAuth 2.0 routes for web-based connection to personal Google Drive.

Requires OAuth 2.0 Web application credentials in Google Cloud Console.
Add redirect URI: http://localhost:8000/oauth/callback (or your server URL).
"""

import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from app.auth.scopes import SCOPES

# In-memory store for OAuth state -> token (one-time use)
_oauth_tokens: dict[str, dict] = {}


def _get_oauth_config() -> tuple[str, str]:
    """Get client_id and client_secret from credentials.json or env."""
    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS") or str(
        Path(__file__).resolve().parent.parent / "credentials.json"
    )
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            data = json.load(f)
        client = data.get("web") or data.get("installed") or {}
        client_id = client.get("client_id") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = client.get("client_secret") or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        return client_id or "", client_secret or ""
    return (
        os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
        os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
    )


def _get_base_url(request: Request) -> str:
    """Get base URL for redirects."""
    if os.environ.get("OAUTH_REDIRECT_URI"):
        uri = os.environ["OAUTH_REDIRECT_URI"].rstrip("/")
        return uri.replace("/oauth/callback", "") if "/oauth/callback" in uri else uri
    return str(request.base_url).rstrip("/")


def _get_redirect_uri(request: Request) -> str:
    """Get redirect URI - use OAUTH_REDIRECT_URI env if set, else derive from request."""
    if os.environ.get("OAUTH_REDIRECT_URI"):
        return os.environ["OAUTH_REDIRECT_URI"].rstrip("/")
    return f"{_get_base_url(request)}/oauth/callback"


async def oauth_start(request: Request):
    """Redirect to Google OAuth consent page."""
    client_id, client_secret = _get_oauth_config()
    if not client_id or not client_secret:
        return JSONResponse(
            {"error": "OAuth not configured. Add credentials.json (web client) or GOOGLE_OAUTH_CLIENT_ID/SECRET."},
            status_code=500,
        )
    redirect_uri = _get_redirect_uri(request)
    state = secrets.token_urlsafe(32)
    _oauth_tokens[state] = {"status": "pending"}
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


async def oauth_callback(request: Request):
    """Handle OAuth callback, exchange code for tokens, redirect to test UI."""
    base_url = _get_base_url(request)
    redirect_uri = _get_redirect_uri(request)
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return RedirectResponse(f"{base_url}/test?oauth_error={error}")

    if not state or not code:
        return RedirectResponse(f"{base_url}/test?oauth_error=missing_params")

    if state not in _oauth_tokens:
        return RedirectResponse(f"{base_url}/test?oauth_error=invalid_state")

    client_id, client_secret = _get_oauth_config()
    if not client_id or not client_secret:
        return RedirectResponse(f"{base_url}/test?oauth_error=config")

    try:
        import requests

        body = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        token_data = resp.json()
    except Exception:
        return RedirectResponse(f"{base_url}/test?oauth_error=exchange")

    oauth_creds = {
        "type": "oauth",
        "token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": SCOPES,
    }
    _oauth_tokens[state] = oauth_creds
    return RedirectResponse(f"{base_url}/test?oauth={state}")


async def oauth_token(request: Request):
    """Return OAuth token for given state (one-time, then deleted)."""
    state = request.query_params.get("state")
    if not state or state not in _oauth_tokens:
        return JSONResponse({"error": "Invalid or expired state"}, status_code=400)
    data = _oauth_tokens.pop(state)
    if data.get("status") == "pending":
        return JSONResponse({"error": "OAuth not complete"}, status_code=400)
    return JSONResponse(data)


async def oauth_info(request: Request):
    """Return the redirect URI being used - add this EXACT URL in Google Cloud Console."""
    redirect_uri = _get_redirect_uri(request)
    return JSONResponse({
        "redirect_uri": redirect_uri,
        "instruction": "Add this EXACT URL to Google Cloud Console → Credentials → OAuth 2.0 Client → Authorized redirect URIs",
    })
