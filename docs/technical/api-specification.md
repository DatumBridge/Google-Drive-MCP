# API Specification (MCP Tools)

## Common contract

Every tool accepts:

- `credentials_path` (optional string)
- `credentials_json` (optional string)

Exactly one must be provided. Failure envelope:

```json
{
  "error_code": "CREDENTIALS_REQUIRED",
  "error_message": "...",
  "retryable": false,
  "original_provider_error": null
}
```

## Tool inventory

39 tools total: 7 Drive + 6 Docs + 8 Sheets + 7 Slides + 6 Forms + 5 draw.io.

See root [README.md](../../README.md) for the full table.

## Create responses

Workspace create tools (`create_document`, `create_spreadsheet`, `create_presentation`, `create_form`) return:

| Field | Meaning |
|-------|---------|
| `parent_applied` | `true` only when parent move succeeded; `false` if omitted or move failed |
| `parent_error` | Standardized error dict when move failed after create; otherwise `null` |

Contract: create success + parent failure ⇒ `success=true`, resource id present, `parent_applied=false`, `parent_error` set. Agents should call `move_file`.

draw.io `create_diagram` sets parents at Drive create time; `parent_applied` is `true` only when a parent was provided and upload succeeded.

## `read_sheet_range`

Input is unchanged: `spreadsheet_id`, `range` (A1). On success, `range` is the authored A1 and `resolved_range` is the A1 actually sent to Sheets (same when no remap). Tab remap never invents cell bounds.

## Error codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| `CREDENTIALS_REQUIRED` | Missing creds | no |
| `INVALID_CREDENTIALS` | Non-OAuth payload | no |
| `AUTH_ERROR` | 401 / expired or revoked token. google-drive-mcp refreshes when vault JSON has `refresh_token` + client id/secret (and when `expiry` is missing). If refresh fails (`invalid_grant`), reconnect Google Drive under Account → Integrations. A Drive `files.list` 400 Invalid Value on `q` is **not** this code. | yes (after refresh or reconnect) |
| `INVALID_QUERY` | Drive `files.list` 400 Invalid Value on `q` (free-text / purchase-request title is not Drive search syntax) | no |
| `PERMISSION_DENIED` | 403 / missing scopes | no |
| `API_NOT_ENABLED` | 403 `SERVICE_DISABLED` — product API (Sheets, Docs, …) not enabled on the OAuth GCP project | yes (after operator enables the API) |
| `OFFICE_FILE_NOT_SUPPORTED` | Drive file is Excel/Office (`.xlsx`), not a native Google Sheet | no |
| `INVALID_RANGE` | Sheets 400 `Unable to parse range` after remap — tab missing or ambiguous; message lists live tab titles when tabs were listed | no |
| `FILE_IN_TRASH` | `spreadsheet_id` still points at a file in Drive Trash | no |
| `NOT_FOUND` | 404 | no |
| `RATE_LIMIT` | 429 | yes |
| `PROVIDER_ERROR` | 5xx | yes |
| `VALIDATION_ERROR` | Bad input | no |
| `PAYLOAD_TOO_LARGE` | Size limit | no |
| `UNSUPPORTED_EXPORT` | draw.io PNG/PDF | no |
| `CONFIRMATION_REQUIRED` | Destructive action needs `confirm=true` | no |
