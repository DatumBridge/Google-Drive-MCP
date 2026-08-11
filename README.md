# Google Drive / Workspace MCP Server

MCP Server for Google Drive and Workspace content (Docs, Sheets, Slides, Forms, draw.io) for the DatumBridge platform. Uses OAuth 2.0 for Personal Google Drive.

## Tools

### Drive (7)

| Tool | Description |
|------|-------------|
| `upload_file` | Upload a file to Google Drive (base64 content or local path) |
| `download_file` | Download a file by ID (returns base64 or text) |
| `list_files` | List files and folders in a folder or root |
| `create_folder` | Create a new folder |
| `move_file` | Move a file to a different parent folder |
| `delete_file` | Permanently delete a file or folder (**requires `confirm=true`**) |
| `get_file_metadata` | Get metadata for a file (name, size, mimeType, etc.) |

### Google Docs (6)

| Tool | Description |
|------|-------------|
| `create_document` | Create a Doc (optional parent folder) |
| `read_document` | Read Doc as plain text |
| `append_document_text` | Append text at end |
| `replace_document_text` | Find/replace all |
| `insert_document_text` | Insert at index (or append) |
| `export_document` | Export as text/PDF/DOCX |

### Google Sheets (8)

| Tool | Description |
|------|-------------|
| `create_spreadsheet` | Create a spreadsheet |
| `list_sheet_tabs` | List tabs |
| `read_sheet_range` | Read A1 range |
| `update_sheet_range` | Write/overwrite range |
| `append_sheet_rows` | Append rows |
| `clear_sheet_range` | Clear range |
| `add_sheet_tab` | Add a tab |
| `export_spreadsheet` | Export csv/xlsx/pdf |

### Google Slides (7)

| Tool | Description |
|------|-------------|
| `create_presentation` | Create a presentation |
| `list_slides` | List slide object IDs |
| `read_presentation` | Extract text per slide |
| `add_slide` | Add a slide |
| `insert_slide_text` | Insert text / create text box |
| `replace_presentation_text` | Deck-wide find/replace |
| `export_presentation` | Export pdf/pptx |

### Google Forms (6)

| Tool | Description |
|------|-------------|
| `create_form` | Create a form |
| `get_form` | Read form structure |
| `update_form_info` | Update title/description |
| `add_form_question` | Add short/paragraph/MC/checkbox question |
| `list_form_responses` | List responses (read-only; answers opt-in via `include_answers`) |
| `get_form_response` | Get one response (answers opt-in) |

### draw.io (5)

| Tool | Description |
|------|-------------|
| `create_diagram` | Create `.drawio` mxfile in Drive |
| `list_diagrams` | List diagram files |
| `read_diagram` | Download diagram XML |
| `update_diagram` | Overwrite diagram content |
| `export_diagram` | Return XML (no server-side PNG/PDF render) |

All files are created in your **Personal Google Drive** (drive.google.com).

## Setup

### 1. Google Cloud Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable APIs: **Drive**, **Docs**, **Sheets**, **Slides**, **Forms**
3. Create **OAuth 2.0 Client ID** (Web application) for the test UI, or Desktop app for the CLI script

### 2. Credentials (Input Parameters)

Credentials are passed as input parameters when invoking each tool:

- **credentials_path**: Path to OAuth token JSON file (e.g. `token.json` from `oauth_connect.py`)
- **credentials_json**: OAuth token JSON as string

**Breaking change:** existing drive-only tokens must **re-consent** (Connect with Google again or re-run `oauth_connect.py`) to obtain Docs/Sheets/Slides/Forms scopes.

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

- **app/mcp_server.py** – FastMCP assembly + HTTP mounts
- **app/auth/** – Shared OAuth scopes, credential loader, API client factory
- **app/tools/** – MCP tool registrations by product
- **app/services/** – Drive/Docs/Sheets/Slides/Forms/Diagram API wrappers
- **app/schemas/** – Pydantic models (DatumBridge ADK uses for Test UI)
- **app/core/exceptions.py** – Normalized error handling
- **docs/** – Architecture, business rules, API spec, ADRs, changelog

See [docs/README.md](docs/README.md) for the full documentation index.

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

```bash
# Structure validation without credentials
./scripts/run_tests.sh

# Full integration (with OAuth token after re-consent)
./scripts/run_tests.sh --credentials-path token.json
```

## Manual Test UI

```bash
open http://localhost:8000/test
```

Click **Connect with Google** to authenticate. The OAuth token is saved to all credential fields automatically.
