# add_slide

Add a slide to a presentation.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `presentation_id` | yes | Presentation ID |
| `layout` | no | Predefined layout (e.g. BLANK, TITLE, TITLE_AND_BODY) |
| `insertion_index` | no | Optional index at which to insert the slide |

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
  "slide_object_id": "example-id"
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
