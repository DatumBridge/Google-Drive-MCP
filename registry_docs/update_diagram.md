# update_diagram

Overwrite draw.io diagram file content in Drive.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | Drive file ID of the .drawio diagram |
| `content_xml` | no | New mxfile XML content |
| `content_base64` | no | New content as base64 (alternative to content_xml) |

## Cases

### Typical call

Input:

```json
{
  "file_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "file_id": "example-id",
  "file_name": "notes.txt",
  "message": "example"
}
```

### Missing `file_id`

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
    "error_message": "file_id is required",
    "retryable": false
  }
}
```
