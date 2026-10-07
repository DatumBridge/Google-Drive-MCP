# move_file

Move a file or folder to a different parent folder.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `file_id` | yes | ID of file or folder to move |
| `new_parent_folder_id` | yes | ID of destination folder |

## Cases

### Typical call

Input:

```json
{
  "file_id": "example-id",
  "new_parent_folder_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "file_id": "example-id",
  "new_parent_id": "example-id",
  "message": "example"
}
```

### Missing `file_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "new_parent_folder_id": "example-id"
}
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
