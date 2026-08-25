from datetime import datetime, timedelta

import json
import pytest

from app.auth.credentials import _parse_expiry, get_credentials
from app.core.exceptions import DriveAuthError, GoogleWorkspaceError


_OAUTH = {
    "type": "oauth",
    "token": "stale-access",
    "refresh_token": "refresh-1",
    "client_id": "cid",
    "client_secret": "csecret",
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": ["https://www.googleapis.com/auth/drive"],
}


def test_parse_expiry_rfc3339():
    expiry = _parse_expiry({"expiry": "2026-08-25T06:00:00Z"})
    assert expiry is not None
    assert expiry.year == 2026
    assert expiry.tzinfo is None


def test_get_credentials_refreshes_when_expiry_missing(monkeypatch):
    def fake_refresh(self, _request):
        self.token = "fresh-access"
        self.expiry = datetime.utcnow() + timedelta(hours=1)

    monkeypatch.setattr("google.oauth2.credentials.Credentials.refresh", fake_refresh)
    creds = get_credentials(credentials_json=json.dumps(_OAUTH))
    assert creds.token == "fresh-access"


def test_get_credentials_skips_refresh_when_expiry_in_future(monkeypatch):
    called = {"n": 0}

    def fake_refresh(self, _request):
        called["n"] += 1

    monkeypatch.setattr("google.oauth2.credentials.Credentials.refresh", fake_refresh)
    payload = {
        **_OAUTH,
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
    }
    creds = get_credentials(credentials_json=json.dumps(payload))
    assert called["n"] == 0
    assert creds.token == "stale-access"


def test_get_credentials_refresh_failure_asks_reconnect(monkeypatch):
    def fake_refresh(self, _request):
        from google.auth.exceptions import RefreshError

        raise RefreshError("invalid_grant")

    monkeypatch.setattr("google.oauth2.credentials.Credentials.refresh", fake_refresh)
    with pytest.raises(DriveAuthError) as ei:
        get_credentials(credentials_json=json.dumps(_OAUTH))
    assert ei.value.error_code == "AUTH_ERROR"
    assert "Integrations" in ei.value.message


def test_get_credentials_missing_bundle_is_credentials_required():
    with pytest.raises(GoogleWorkspaceError) as ei:
        get_credentials(credentials_json=None, credentials_path=None)
    assert ei.value.error_code == "CREDENTIALS_REQUIRED"
