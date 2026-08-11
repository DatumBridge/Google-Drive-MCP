# System Overview

## Role

`google-drive-mcp` is a **stateless MCP tool server** that exposes Google Drive and Workspace content APIs (Docs, Sheets, Slides, Forms) plus draw.io diagram files stored in Drive.

It is a tool server, not a token vault / multi-tenant relay. Callers pass OAuth credentials per invocation (`credentials_path` or `credentials_json`).

## What changed (Workspace expansion)

| Area | Change |
|------|--------|
| Products | Added Docs, Sheets, Slides, Forms, draw.io tools (39 total) |
| Auth | Shared factory + expanded OAuth scopes (re-consent required) |
| Layout | Tools/services/schemas split by domain; `mcp_server.py` is assembly-only |
| MCP name | Remains `google-drive` for registry compatibility |
| Create-with-parent | Soft-fail: create success + move failure ⇒ `success=true`, resource id kept, `parent_applied=false`, `parent_error` set; agents recover via `move_file` (ADR-0004) |

## Impacted components

- `app/auth/` — scopes, credentials, clients
- `app/tools/` — tool registration modules
- `app/services/` — API wrappers
- `app/schemas/` — response models
- OAuth routes + `scripts/oauth_connect.py`

## Non-goals (this release)

- Encrypted multi-tenant token store
- Webhooks / Drive Activity
- Server-side diagrams.net PNG/PDF rendering
- Shared Drives admin APIs
- Progressive per-tool OAuth scopes (full `drive` retained; see ADR-0002)
