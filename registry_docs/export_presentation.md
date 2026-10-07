# export_presentation

Export a presentation via Drive export (pdf/pptx).

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `presentation_id` | yes | Presentation ID |
| `export_format` | no | Export format: pdf or pptx |

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
  "mime_type": "example",
  "content_base64": "example"
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
