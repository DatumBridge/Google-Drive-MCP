# list_form_responses

List form responses (read-only). Set include_answers=true only when answer payloads are required.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `form_id` | yes | Form ID |
| `page_size` | no | Max responses per page |
| `page_token` | no | Pagination token |
| `include_answers` | no | Opt-in to include answer payloads (may contain PII; default false) |

## Cases

### Typical call

Input:

```json
{
  "form_id": "example-id"
}
```

Output:

```json
{
  "success": true,
  "form_id": "example-id",
  "responses": [],
  "next_page_token": "example"
}
```

### Missing `form_id`

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
    "error_message": "form_id is required",
    "retryable": false
  }
}
```
