# read_sheet_range

Read values from a spreadsheet range (A1 notation).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `range` | yes | A1 notation range, e.g. Sheet1!A1:C10 |

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
  "range": "example",
  "resolved_range": "example",
  "values": []
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
