# insert_document_text

Insert text at an optional Docs index, or append when index is omitted.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `document_id` | yes | Google Docs document ID |
| `text` | yes | Text to insert |
| `index` | no | Optional Docs body index (>=1). Omit to append at end. |

## Cases

### Typical call

Input:

```json
{
  "document_id": "example-id",
  "text": "hello"
}
```

Output:

```json
{
  "success": true,
  "document_id": "example-id",
  "message": "example"
}
```

### Missing `document_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "text": "hello"
}
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
