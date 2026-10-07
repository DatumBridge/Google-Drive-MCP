# create_folder

Create a new folder in Google Drive.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `folder_name` | yes | Name for the new folder |
| `parent_folder_id` | no | Parent folder ID (omit for root) |

## Cases

### Typical call

Input:

```json
{
  "folder_name": "example"
}
```

Output:

```json
{
  "success": true,
  "folder_id": "example-id",
  "folder_name": "example",
  "web_view_link": "example"
}
```

### Missing `folder_name`

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
    "error_message": "folder_name is required",
    "retryable": false
  }
}
```
