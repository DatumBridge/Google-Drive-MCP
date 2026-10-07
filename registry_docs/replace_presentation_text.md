# replace_presentation_text

Find and replace text across an entire presentation.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `presentation_id` | yes | Presentation ID |
| `find_text` | yes | Text to find |
| `replace_text` | yes | Replacement text |
| `match_case` | no | Case-sensitive match |

## Cases

### Typical call

Input:

```json
{
  "presentation_id": "example-id",
  "find_text": "example",
  "replace_text": "example"
}
```

Output:

```json
{
  "success": true,
  "presentation_id": "example-id",
  "occurrences_changed": "example",
  "message": "example"
}
```

### Missing `presentation_id`

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
    "error_message": "presentation_id is required",
    "retryable": false
  }
}
```
