# delete_file

Permanently delete a file or folder from Google Drive. This bypasses trash — the file cannot be recovered. Requires confirm=true as an explicit agent/operator gate.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | ID of file or folder to delete |
| `confirm` | no | Must be true to permanently delete (bypasses trash; irreversible) |

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
