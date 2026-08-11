# Security Architecture

## Trust model

- User OAuth tokens authorize Google API calls as that user
- Server does not store long-lived user tokens in a database
- In-memory OAuth state map is one-time for the Connect UI flow
- Prefer `credentials_path` over `credentials_json` in agent runtimes so refresh tokens are less likely to enter model transcripts

## Controls

| Control | Behavior |
|---------|----------|
| Least privilege (Forms responses) | `forms.responses.readonly` only |
| Forms answers default off | `include_answers=false` unless explicitly opted in |
| Deny without creds | `CREDENTIALS_REQUIRED` |
| No secret logging | Tokens / response PII not logged |
| Payload limits | Export ≤ 25MB; diagram ≤ 5MB; diagram XML to agents ≤ 200k chars; sheet cells ≤ 50k |
| Permanent delete gate | `delete_file` requires `confirm=true` |
| Create-with-parent | Soft-fail keeps resource id; no privilege escalation on move 403 |
| Untrusted content | Docs/Sheets/diagram/Form text returned to agents is untrusted input — host agents should isolate it from instructions |

## Scope expansion risk

Re-consent is mandatory. Old drive-only tokens fail content APIs with 403 until refreshed. Full `drive` scope is intentional (ADR-0002) and high blast-radius if a token leaks.
