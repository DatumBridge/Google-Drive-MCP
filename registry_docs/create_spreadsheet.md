# create_spreadsheet

Create a Google Spreadsheet. Optionally place it in a Drive folder.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `title` | no | Spreadsheet title |
| `sheet_titles` | no | Optional initial sheet/tab titles |
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
  "spreadsheet_id": "example-id",
  "title": "Status update",
  "spreadsheet_url": "https://example.com/page",
  "parent_applied": "example",
  "parent_error": "example"
}
```
