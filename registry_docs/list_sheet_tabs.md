# list_sheet_tabs

List sheet tabs (title + sheetId) in a spreadsheet.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |

## Cases

### Typical call

Input:

```json
{
  "spreadsheet_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "spreadsheet_id": "example-id",
  "tabs": []
}
```

### Missing `spreadsheet_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{}
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
