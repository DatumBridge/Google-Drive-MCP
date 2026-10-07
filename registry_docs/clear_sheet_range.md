# clear_sheet_range

Clear values in a spreadsheet range.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `range` | yes | A1 notation range to clear |

## Cases

### Typical call

Input:

```json
{
  "spreadsheet_id": "example-id",
  "range": "example"
}
```

Output:

```json
{
  "success": true,
  "spreadsheet_id": "example-id",
  "cleared_range": "example"
}
```

### Missing `spreadsheet_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "range": "example"
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
