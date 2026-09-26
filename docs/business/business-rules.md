# Business Rules

1. Every tool requires `credentials_path` or `credentials_json`.
2. Existing Drive tool names and behaviors remain stable.
3. Create-with-parent: Workspace creates via product API, then Drive parent move. Responses include `parent_applied` and optional `parent_error`. If create succeeds but move fails, keep `success=true` with the resource id so agents can call `move_file`.
4. Diagrams are Drive files (mxfile); there is no Draw.io Google API.
5. Form response tools are read-only; `include_answers` defaults to `false` (opt-in for PII-bearing answers).
6. Prefer semantic Docs/Slides helpers (`append_*`, `replace_*`) over raw index math.
7. Exports above size limits fail with `PAYLOAD_TOO_LARGE`.
8. Rate limits (`429`) are marked `retryable=true`. Product APIs that are not enabled on the OAuth GCP project (`SERVICE_DISABLED`) return `API_NOT_ENABLED` (`retryable=true` after the operator enables the API). That is not a Drive sharing ACL and not `CREDENTIALS_REQUIRED`.
9. `read_sheet_range` and other Sheets API tools require a **native Google Sheet** (`application/vnd.google-apps.spreadsheet`). An uploaded Excel `.xlsx` in Drive returns `OFFICE_FILE_NOT_SUPPORTED`. Convert in Drive (Open with → Google Sheets) once; do not pass the `.xlsx` file id.
10. `read_sheet_range` keeps authored cell bounds. If the tab in `range` does not exist, it remaps the tab (quoted title, case / underscore-vs-space, unique budget/ngân sách **word**, or convert-default `Sheet1`). Unrelated singleton tabs and several unmatched tabs return `INVALID_RANGE` with the live titles. Google 400 `Unable to parse range` is `INVALID_RANGE`, not `VALIDATION_ERROR`. Success includes `resolved_range`.
11. `delete_file` requires `confirm=true` or returns `CONFIRMATION_REQUIRED`.
12. Drive `list_files` `query` must be Drive search syntax (or free text, which is wrapped as `name contains '...'`). A Google 400 Invalid Value on `q` is `INVALID_QUERY`, never `AUTH_ERROR` (do not match `pageToken` in the URL as an OAuth token).
