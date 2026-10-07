# get_file_metadata

Get metadata for a file or folder (name, size, mimeType, timestamps, etc.).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | Google Drive file ID |

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
  "metadata": "example"
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
