# append_document_text

Append text to the end of a Google Doc (hides raw index math).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `document_id` | yes | Google Docs document ID |
| `text` | yes | Text to append at the end of the document |

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
