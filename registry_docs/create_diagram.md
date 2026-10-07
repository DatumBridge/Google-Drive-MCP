# create_diagram

Create a draw.io (.drawio) diagram file in Google Drive.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `name` | no | Diagram file name |
| `content_xml` | no | Optional mxfile XML; defaults to empty diagram |
| `parent_folder_id` | no | Optional Drive parent folder ID |

## Cases

### Typical call

Input:

```json
{}
```

Output:

```json
{
  "success": true,
  "file_id": "example-id",
  "file_name": "notes.txt",
  "web_view_link": "example",
  "parent_applied": "example",
  "parent_error": "example"
}
```
