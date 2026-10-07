# download_file

Download a file from Google Drive by ID. Returns content as base64 (default) or plain text for text files.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | Google Drive file ID to download |
| `as_text` | no | If true, return content as text. If false, return base64 for binary files. |

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
  "content_base64": "example",
  "content_text": "example",
  "mime_type": "example"
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
