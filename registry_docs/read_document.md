# read_document

Read a Google Doc as plain text.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `document_id` | yes | Google Docs document ID |

## Cases

### Typical call

Input:

```json
{
  "document_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "document_id": "example-id",
  "title": "Status update",
  "text": "hello",
  "revision_id": "example-id"
}
```

### Missing `document_id`

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
    "error_message": "document_id is required",
    "retryable": false
  }
}
```
