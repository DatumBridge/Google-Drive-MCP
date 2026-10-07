# append_sheet_rows

Append rows to a spreadsheet sheet/table.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `values` | yes | 2D array of rows to append, or JSON string |
| `range` | no | Sheet/table range to append into (A1 notation or sheet name) |
| `value_input_option` | no | RAW or USER_ENTERED |

## Cases

### Typical call

Input:

```json
{
  "spreadsheet_id": "example-id",
  "values": [
    "example"
  ]
}
```

Output:

```json
{
  "success": true,
  "spreadsheet_id": "example-id",
  "updated_range": "2026-09-08",
  "updated_rows": []
}
```

### Missing `spreadsheet_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "values": [
    "example"
  ]
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
