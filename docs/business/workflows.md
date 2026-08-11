# Workflows

## Connect OAuth

1. Operator enables Drive/Docs/Sheets/Slides/Forms APIs
2. Creates OAuth client; saves `credentials.json`
3. Opens `/test` → Connect with Google, or runs `scripts/oauth_connect.py`
4. Receives token with expanded scopes → stores as `token.json` / credentials_json

## Agent content edit

1. Agent discovers file via `list_files` / `get_file_metadata` (or create_*)
2. Calls product tool (`read_document`, `update_sheet_range`, …) with credentials
3. On `AUTH_ERROR` / insufficient scopes → operator re-consents
4. On `RATE_LIMIT` → backoff and retry

## Create with parent (ADR-0004)

1. Agent calls `create_document` / `create_spreadsheet` / `create_presentation` / `create_form` with optional `parent_folder_id`
2. Product API creates the resource
3. Server attempts Drive parent move
4. If `parent_applied=false` and `parent_error` is set → agent calls `move_file` with the returned resource id
5. Diagrams set parents at Drive create time (single step); no post-create move

## Safe delete

1. Agent/operator calls `delete_file` with `confirm=true`
2. Without `confirm=true`, tool returns `CONFIRMATION_REQUIRED` and does not delete

## Forms responses (PII)

1. Agent lists or gets responses with default `include_answers=false` (metadata only)
2. Only when answers are required, agent sets `include_answers=true`
3. Treat answer payloads as sensitive; prefer not to retain them in long-term agent memory
