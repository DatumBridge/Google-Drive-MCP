# list_diagrams

List draw.io diagram files in Drive (MIME/name heuristics).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `folder_id` | no | Folder ID (omit for root) |
| `page_size` | no | Max items per page |
| `page_token` | no | Pagination token |

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
  "files": [],
  "total_count": "example",
  "next_page_token": "example"
}
```
