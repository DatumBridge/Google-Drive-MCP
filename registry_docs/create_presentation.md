# create_presentation

Create a Google Slides presentation.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `title` | no | Presentation title |
| `parent_folder_id` | no | Optional Drive parent folder ID |
| `slides` | no | Slide content as a JSON array of {title, body}. Plain text is written as one slide. Do not pass []. |
| `description` | no | Body of the first slide when slides is empty. Used so the deck is not created blank. |

## Cases

### Typical call

Input:

```json
{}
```

Output:

```json
{
  "success": true,
  "presentation_id": "example-id",
  "title": "Status update",
  "presentation_url": "https://example.com/page",
  "parent_applied": "example",
  "parent_error": "example",
  "slides_written": "example"
}
```
