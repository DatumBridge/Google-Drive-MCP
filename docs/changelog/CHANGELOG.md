# Changelog

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
