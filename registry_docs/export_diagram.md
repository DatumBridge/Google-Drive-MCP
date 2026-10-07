# export_diagram

Export diagram content. Server returns XML; no diagrams.net render API.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | Drive file ID of the .drawio diagram |
| `export_format` | no | xml (default). PNG/PDF conversion is not available server-side. |

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
  "mime_type": "example",
  "content_xml": "example",
  "content_base64": "example",
  "note": "example"
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
