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

## Error codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| `CREDENTIALS_REQUIRED` | Missing creds | no |
| `INVALID_CREDENTIALS` | Non-OAuth payload | no |
| `AUTH_ERROR` | 401 / expired token | yes |
| `PERMISSION_DENIED` | 403 / missing scopes | no |
| `NOT_FOUND` | 404 | no |
| `RATE_LIMIT` | 429 | yes |
| `PROVIDER_ERROR` | 5xx | yes |
| `VALIDATION_ERROR` | Bad input | no |
| `PAYLOAD_TOO_LARGE` | Size limit | no |
| `UNSUPPORTED_EXPORT` | draw.io PNG/PDF | no |
| `CONFIRMATION_REQUIRED` | Destructive action needs `confirm=true` | no |
