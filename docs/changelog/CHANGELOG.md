# Changelog

## 2026-08-25

### Fixed

- **Drive 400 Invalid Value on `q` was reported as `AUTH_ERROR`.** Catalog `list_files` sent purchase-request text (`mua phần mềm CRM zoho`) as Drive `q`. The error URL contains `pageToken`, so `"invalid" and "token"` mapped to “Token expired or invalid”. 400 invalid `q` is now `INVALID_QUERY` and includes the original Google message. Free text is wrapped as `name contains '...'`. LangGraph does not auto-fill unbound `list_files` query from catalog start-form text. Redeploy `google-drive-mcp` and `datumbridge-langgraph`.
- **Google Drive `list_files` AUTH_ERROR “Token expired or invalid”.** Vault inject had `refresh_token` but no `expiry`, so google-auth sent the stale access token and Google returned 401 without refresh. MCP now refreshes before Drive calls; Integrations stores `expiry` on Connect. If refresh still fails, Disconnect then Connect Google Drive. Redeploy `google-drive-mcp` and `datumbridge-integrations`.
- **403 `SERVICE_DISABLED` was reported as `PERMISSION_DENIED`.** Google Sheets/Docs/Slides/Forms 403 with `has not been used in project` / `SERVICE_DISABLED` now returns `API_NOT_ENABLED` with the Console activation URL. Enable the product API on the OAuth client project, wait a few minutes, retry. Not a Drive ACL and not an Integrations reconnect. Redeploy `google-drive-mcp`.
- **Sheets API 400 “Unable to parse range”.** Converted Excel workbooks often keep a process-contract tab such as `Budget_2026` while the live tab is `Sheet1` or `Budget 2026`. `read_sheet_range` quotes the title, then remaps a missing tab (case / underscore-vs-space / unique budget **word** / convert-default `Sheet1`) while keeping the authored cells (`A1:Z200`). Unrelated singleton tabs and ambiguous tabs fail with `INVALID_RANGE` and list real titles. Success includes `resolved_range`. Redeploy `google-drive-mcp`. See ADR-0005.
- **Sheets API 400 “must not be an Office file”.** Uploaded `.xlsx` Drive files are not native Google Sheets. `read_sheet_range` now checks Drive mime first and returns `OFFICE_FILE_NOT_SUPPORTED`. Convert in Drive (Open with → Google Sheets) and use the new file id. Redeploy `google-drive-mcp`.
- **Deleted Drive files still used by catalog `spreadsheet_id`.** `files.get` returns Trash by id. `list_files` adds `trashed = false`. Trashed sheet ids return `FILE_IN_TRASH`. Redeploy `google-drive-mcp`.

## 2026-08-11

### Added

- Google Docs tools: create, read, append, replace, insert, export
- Google Sheets tools: create, tabs, read/update/append/clear, export
- Google Slides tools: create, list/read, add slide, insert/replace text, export
- Google Forms tools: create, get, update info, add question, list/get responses
- draw.io tools: create, list, read, update, export (Drive mxfile)
- Shared auth factory (`app/auth/`) and domain tool/service/schema modules
- Documentation tree under `/docs` (architecture, business, technical, ADRs)

### Changed

- OAuth scopes expanded (re-consent required for existing tokens)
- `mcp_server.py` is assembly-only; tools live under `app/tools/`
- `DriveError` aliased to `GoogleWorkspaceError`
- Forms `include_answers` defaults to `false` (PII opt-in)
- `delete_file` requires `confirm=true`

### Fixed

- Create-with-parent soft-fail: parent move failures no longer hide created Docs/Sheets/Slides/Forms IDs (`parent_applied=false` + `parent_error`)
- Docs/Slides create keeps resource id if post-create metadata fetch fails
- draw.io agent reads truncate XML above 200k chars

### Removed

- N/A (existing 7 Drive tools retained)
