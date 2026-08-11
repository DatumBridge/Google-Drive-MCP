#!/usr/bin/env python3
"""
OAuth 2.0 connection script for personal Google Drive / Workspace.

Run this once to authorize the MCP tools to access your personal Google Drive,
Docs, Sheets, Slides, and Forms. Opens a browser for you to sign in.

Usage:
    1. In Google Cloud Console: APIs & Services → Credentials
       Create OAuth 2.0 Client ID (Desktop app or Web application)
       Download the JSON and save as credentials.json

    2. Enable APIs: Drive, Docs, Sheets, Slides, Forms

    3. Run this script:
       python scripts/oauth_connect.py

    4. Sign in with your Google account in the browser

    5. The script saves token.json - use this with MCP tools:
       - credentials_path: path to token.json
       - Or paste contents of token.json as credentials_json

Note: If you previously connected with drive-only scopes, re-run this script
to re-consent for Docs/Sheets/Slides/Forms.
"""

import json
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: pip install google-auth-oauthlib")
    sys.exit(1)

from app.auth.scopes import SCOPES

CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent / "token.json"


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"Error: {CREDENTIALS_FILE} not found.")
        print()
        print("Create OAuth 2.0 credentials:")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Create OAuth 2.0 Client ID (Desktop app)")
        print("  3. Download JSON and save as credentials.json in the project root")
        sys.exit(1)

    print("Opening browser for Google sign-in...")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), SCOPES
    )
    creds = flow.run_local_server(port=0)

    token_data = {
        "type": "oauth",
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nSuccess! Token saved to {TOKEN_FILE}")
    print()
    print("Use with MCP tools:")
    print(f"  credentials_path: {TOKEN_FILE}")
    print("  Or paste the contents of token.json as credentials_json")
    print()
    print("Your personal Google Drive is now accessible via the MCP tools.")


if __name__ == "__main__":
    main()
