# Deployment Architecture

## Local / Docker

- HTTP: `uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000`
- Stdio: `python -m app.mcp_server`
- Docker image exposes port 8000; health at `/health`

## Credentials

- OAuth client secrets: `credentials.json` (for Connect UI / CLI only)
- User tokens: `token.json` or per-call `credentials_json`
- Do not bake user tokens into images

## K8s notes

Same pattern as other DatumBridge MCP tool servers: deploy as a Service, pass credentials at tool-call time from the agent runtime / Test UI.
