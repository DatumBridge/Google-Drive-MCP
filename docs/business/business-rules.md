# Business Rules

1. Every tool requires `credentials_path` or `credentials_json`.
2. Existing Drive tool names and behaviors remain stable.
3. Create-with-parent: Workspace creates via product API, then Drive parent move. Responses include `parent_applied` and optional `parent_error`. If create succeeds but move fails, keep `success=true` with the resource id so agents can call `move_file`.
4. Diagrams are Drive files (mxfile); there is no Draw.io Google API.
5. Form response tools are read-only; `include_answers` defaults to `false` (opt-in for PII-bearing answers).
6. Prefer semantic Docs/Slides helpers (`append_*`, `replace_*`) over raw index math.
7. Exports above size limits fail with `PAYLOAD_TOO_LARGE`.
8. Rate limits (`429`) are marked `retryable=true`.
9. `delete_file` requires `confirm=true` or returns `CONFIRMATION_REQUIRED`.
