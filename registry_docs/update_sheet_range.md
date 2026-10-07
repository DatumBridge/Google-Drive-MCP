# update_sheet_range

Overwrite a spreadsheet range with values.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `range` | yes | A1 notation range to write |
| `values` | yes | 2D array of values, or JSON string of 2D array |
| `value_input_option` | no | RAW or USER_ENTERED |

## Cases

### Typical call

Input:

```json
{
  "spreadsheet_id": "example-id",
  "range": "example",
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
  "updated_rows": [],
  "updated_columns": [],
  "updated_cells": []
}
```

### Missing `spreadsheet_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "range": "example",
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
