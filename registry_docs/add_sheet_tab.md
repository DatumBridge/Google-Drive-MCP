# add_sheet_tab

Add a new tab to a spreadsheet.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `title` | yes | New tab title |

## Cases

### Typical call

Input:

```json
{
  "spreadsheet_id": "example-id",
  "title": "Status update"
}
```

Output:

```json
{
  "success": true,
  "spreadsheet_id": "example-id",
  "sheet_id": "example-id",
  "title": "Status update"
}
```

### Missing `spreadsheet_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "title": "Status update"
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "spreadsheet_id is required",
    "retryable": false
  }
}
```
