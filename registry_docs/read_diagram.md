# read_diagram

Download draw.io diagram XML/content from Drive.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | Drive file ID of the .drawio diagram |

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
  "mime_type": "example",
  "content_xml": "example",
  "content_base64": "example",
  "truncated": "example"
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
