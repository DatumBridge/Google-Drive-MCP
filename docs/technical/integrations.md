# Integrations

| Integration | Library / API |
|-------------|---------------|
| Drive v3 | `googleapiclient` `drive` |
| Docs v1 | `docs` |
| Sheets v4 | `sheets` (`read_sheet_range` remaps a missing tab; keeps authored cells; ADR-0005) |
| Slides v1 | `slides` |
| Forms v1 | `forms` |
| draw.io | Drive file media only (`application/vnd.jgraph.mxfile`) |
| MCP | FastMCP |
| HTTP | Starlette + uvicorn |

DatumBridge ADK Test UI regenerates forms from Pydantic schemas under `app/schemas/`.
