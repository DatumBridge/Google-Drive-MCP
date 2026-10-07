# create_document

Create a Google Doc. Optionally move it into a Drive folder (parent_applied reports success).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `title` | no | Document title |
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
  "document_id": "example-id",
  "title": "Status update",
  "web_view_link": "example",
  "parent_applied": "example",
  "parent_error": "example"
}
```
