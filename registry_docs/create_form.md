# create_form

Create a Google Form.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `title` | no | Form title |
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
  "form_id": "example-id",
  "title": "Status update",
  "responder_uri": "example",
  "parent_applied": "example",
  "parent_error": "example"
}
```
