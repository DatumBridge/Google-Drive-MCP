# add_form_question

Add a question to a Google Form.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `form_id` | yes | Form ID |
| `title` | yes | Question title/prompt |
| `question_type` | no | short_answer / paragraph / multiple_choice / checkbox |
| `options` | no | Required for multiple_choice and checkbox |
| `required` | no | Whether the question is required |
| `index` | no | Insertion index in the form |

## Cases

### Typical call

Input:

```json
{
  "form_id": "example-id",
  "title": "Status update"
}
```

Output:

```json
{
  "success": true,
  "form_id": "example-id",
  "item_id": "example-id",
  "question_id": "example-id"
}
```

### Missing `form_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "title": "Status update"
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
