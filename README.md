# Google Drive MCP Server

MCP Server for Google Drive integration with the DatumBridge platform. Exposes Drive capabilities as standardized MCP tools. Uses OAuth 2.0 for Personal Google Drive.

## Tools

| Tool | Description |
|------|-------------|
| `upload_file` | Upload a file to Google Drive (base64 content or local path) |
| `download_file` | Download a file by ID (returns base64 or text) |
| `list_files` | List files and folders in a folder or root |
| `create_folder` | Create a new folder |
| `move_file` | Move a file to a different parent folder |
| `delete_file` | Permanently delete a file or folder |
| `get_file_metadata` | Get metadata for a file (name, size, mimeType, etc.) |

All files are created in your **Personal Google Drive** (drive.google.com).

## Setup

### 1. Google Cloud Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the **Google Drive API**
3. Create **OAuth 2.0 Client ID** (Web application) for the test UI, or Desktop app for the CLI script

### 2. Credentials (Input Parameters)

Credentials are passed as input parameters when invoking each tool:

- **credentials_path**: Path to OAuth token JSON file (e.g. `token.json` from `oauth_connect.py`)
- **credentials_json**: OAuth token JSON as string

### 3. Install Dependencies

```bash
pip install -r requirements_mcp.txt
```

## Running

### Stdio mode (for Claude Desktop, Cursor)

```bash
python -m app.mcp_server
```

### HTTP/SSE mode

```bash
uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
# Or
./mcp_server_entrypoint.sh
```

### Docker

```bash
docker build -t google-drive-mcp .
docker run -p 8000:8000 google-drive-mcp
```

- **Health check**: `curl http://localhost:8000/health` returns `{"status":"ok","service":"google-drive-mcp"}`
- **MCP endpoints**: Available at `/mcp/` (Streamable HTTP) and `/sse/` (SSE transport)
- Credentials are passed per tool invocation (credentials_path or credentials_json)

## Architecture

- **app/mcp_server.py** – MCP server with FastMCP, tool definitions
- **app/services/drive_service.py** – Google Drive API wrapper (OAuth only)
- **app/schemas/mcp_models.py** – Pydantic models for inputs/outputs (DatumBridge ADK uses for Test UI)
- **app/core/exceptions.py** – Normalized error handling

## OAuth: Connect Your Personal Google Drive

### Option A: Test UI (in-browser)

1. Create **OAuth 2.0 Client ID** (Web application) in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add the **exact** redirect URI to Authorized redirect URIs. Check http://localhost:8000/oauth/info for the URL your server uses (often `http://localhost:8000/oauth/callback`).
3. Download the JSON and save as `credentials.json` in the project root
4. Start the server and open http://localhost:8000/test
5. Click **Connect with Google** → sign in → OAuth token is saved to all forms

**redirect_uri_mismatch?** The URI must match exactly (no trailing slash, correct host/port). Use `OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback` if needed.

### Option B: CLI script

1. Create **OAuth 2.0 Client ID** (Desktop app) in Google Cloud Console
2. Save as `credentials.json` in the project root
3. Run: `python scripts/oauth_connect.py`
4. Use `token.json` as credentials_path or credentials_json

Files you create will appear in **your personal Google Drive** (drive.google.com).

## Testing

Run the test script to verify all 7 MCP tools:

```bash
# 1. Start server
docker run -d -p 8000:8000 --name google-drive-mcp google-drive-mcp

# 2. Run tests (structure validation without credentials)
./scripts/run_tests.sh

# 3. Full integration (with OAuth token)
./scripts/run_tests.sh --credentials-path token.json
```

## Manual Test UI

```bash
# Start server
docker run -d -p 8000:8000 --name google-drive-mcp google-drive-mcp

# Open in browser
open http://localhost:8000/test
```

Click **Connect with Google** to authenticate. The OAuth token is saved to all credential fields automatically.
