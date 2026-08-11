# Component Diagram

```text
┌─────────────────────────────────────────────────────────┐
│ mcp_server.py (FastMCP + Starlette /health,/test,/oauth)│
└───────────────────────────┬─────────────────────────────┘
                            │ register_all()
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   drive_tools         docs/sheets/…        diagram_tools
        │                   │                   │
        ▼                   ▼                   ▼
   DriveService        Docs/Sheets/…       DiagramService
        │              Slides/Forms             │
        └───────────────────┬───────────────────┘
                            ▼
                     app/auth/clients
                            ▼
              Google Drive / Docs / Sheets / Slides / Forms APIs
```

Dependency direction: `tools → services → auth → Google APIs`.
Product services may call `DriveService` public helpers (parent move, export) only.
