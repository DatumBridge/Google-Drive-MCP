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

Drive, Docs, Sheets, Slides, Forms.
