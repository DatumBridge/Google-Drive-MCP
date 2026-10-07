# upload_file

Upload a file to Google Drive. Provide either content_base64 (for MCP clients) or file_path (for server-side files). Credentials must be passed as credentials_path or credentials_json.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_name` | yes | Name for the uploaded file |
| `content_base64` | no | File content as base64-encoded string (use for binary or text) |
| `file_path` | no | Local file path to upload (when running on server with file access) |
| `parent_folder_id` | no | ID of parent folder (omit for root) |
| `mime_type` | no | MIME type (e.g., text/plain, application/pdf). Auto-detected from file_path if not provided. |

## Cases

### Typical call

Input:

```json
{
  "file_name": "notes.txt"
}
```

Output:

```json
{
  "success": true,
  "file_id": "example-id",
  "file_name": "notes.txt",
  "web_view_link": "example"
}
```

### Missing `file_name`

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
    "error_message": "file_name is required",
    "retryable": false
  }
}
```
