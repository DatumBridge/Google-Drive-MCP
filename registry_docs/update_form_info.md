# update_form_info

Update form title and/or description.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `form_id` | yes | Form ID |
| `title` | no | New form title |
| `description` | no | New form description |

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
  "message": "example"
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
