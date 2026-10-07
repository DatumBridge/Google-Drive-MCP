# export_spreadsheet

Export a spreadsheet via Drive export (csv/xlsx/pdf).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `spreadsheet_id` | yes | Spreadsheet ID |
| `export_format` | no | Export format: csv, xlsx, or pdf |

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
  "mime_type": "example",
  "content_base64": "example",
  "content_text": "example"
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
