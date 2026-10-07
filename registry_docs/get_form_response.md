# get_form_response

Get a single form response by ID (read-only). Set include_answers=true to load answers.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `form_id` | yes | Form ID |
| `response_id` | yes | Response ID |
| `include_answers` | no | Opt-in to include answer payloads (may contain PII; default false) |

## Cases

### Typical call

Input:

```json
{
  "form_id": "example-id",
  "response_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "form_id": "example-id",
  "response_id": "example-id",
  "create_time": "example",
  "last_submitted_time": "example",
  "answers": []
}
```

### Missing `form_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "response_id": "example-id"
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "form_id is required",
    "retryable": false
  }
}
```
