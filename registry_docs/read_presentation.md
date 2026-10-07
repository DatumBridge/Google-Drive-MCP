# read_presentation

Extract text content per slide for agent-friendly reading.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `presentation_id` | yes | Presentation ID |

## Cases

### Typical call

Input:

```json
{
  "presentation_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "presentation_id": "example-id",
  "title": "Status update",
  "slides": []
}
```

### Missing `presentation_id`

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
    "error_message": "presentation_id is required",
    "retryable": false
  }
}
```
