# insert_slide_text

Insert text into a shape, or create a text box on a slide.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `presentation_id` | yes | Presentation ID |
| `text` | yes | Text to insert |
| `slide_object_id` | no | Target slide object ID (defaults to first slide) |
| `shape_object_id` | no | Existing shape object ID to insert into |

## Cases

### Typical call

Input:

```json
{
  "presentation_id": "example-id",
  "text": "hello"
}
```

Output:

```json
{
  "success": true,
  "presentation_id": "example-id",
  "message": "example"
}
```

### Missing `presentation_id`

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
    "error_message": "presentation_id is required",
    "retryable": false
  }
}
```
