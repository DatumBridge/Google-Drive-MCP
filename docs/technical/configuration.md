# Configuration

## Environment variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_OAUTH_CREDENTIALS` | Path to OAuth client `credentials.json` |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | Override client secrets |
| `OAUTH_REDIRECT_URI` | Exact redirect URI for web OAuth |

Tool calls do **not** read user tokens from the environment.

## OAuth scopes (source of truth: `app/auth/scopes.py`)

- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/presentations`
- `https://www.googleapis.com/auth/forms.body`
- `https://www.googleapis.com/auth/forms.responses.readonly`

## GCP APIs to enable

On the **same** Google Cloud project as the OAuth client (`GOOGLE_OAUTH_CLIENT_ID`):

| API | Console |
|-----|---------|
| Google Drive API | `https://console.cloud.google.com/apis/api/drive.googleapis.com/overview` |
| Google Sheets API | `https://console.cloud.google.com/apis/api/sheets.googleapis.com/overview` |
| Google Docs API | `https://console.cloud.google.com/apis/api/docs.googleapis.com/overview` |
| Google Slides API | `https://console.cloud.google.com/apis/api/slides.googleapis.com/overview` |
| Google Forms API | `https://console.cloud.google.com/apis/library/forms.googleapis.com` |

`list_files` only needs Drive. `read_sheet_range` / `create_spreadsheet` need **Sheets** as well. A 403 `SERVICE_DISABLED` / `API_NOT_ENABLED` means enable that product API, wait a few minutes, and retry — do not reconnect Integrations.

Uploaded **Excel `.xlsx` files in Drive are not Google Sheets**. `read_sheet_range` returns `OFFICE_FILE_NOT_SUPPORTED`. Convert: Drive → Open with → Google Sheets, then use the new native file id.
