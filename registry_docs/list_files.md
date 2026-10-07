# list_files

List files and folders in a Google Drive folder. Returns file metadata including id, name, mimeType, size, timestamps.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `folder_id` | no | Folder ID to list (omit for root) |
| `page_size` | no | Max items per page (1-1000) |
| `page_token` | no | Token for next page (from previous list_files response) |
| `query` | no | Optional Drive query (e.g. mimeType='application/vnd.google-apps.spreadsheet'). Free text is wrapped as name contains '...'. |

## Cases

### Typical call

Input:

```json
{
  "query": "quarterly report"
}
```

Output:

```json
{
  "success": true,
  "files": [],
  "total_count": "example",
  "next_page_token": "example"
}
```
