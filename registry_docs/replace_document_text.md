# replace_document_text

Find and replace all matching text in a Google Doc.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `document_id` | yes | Google Docs document ID |
| `find_text` | yes | Text to find |
| `replace_text` | yes | Replacement text |
| `match_case` | no | Case-sensitive match |

## Cases

### Typical call

Input:

```json
{
  "document_id": "example-id",
  "find_text": "example",
  "replace_text": "example"
}
```

Output:

```json
{
  "success": true,
  "document_id": "example-id",
  "occurrences_changed": "example",
  "message": "example"
}
```

### Missing `document_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "find_text": "example",
  "replace_text": "example"
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
