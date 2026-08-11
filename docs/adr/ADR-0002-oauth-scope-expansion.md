# ADR-0002 — OAuth Scope Expansion

## Context

Content APIs require Docs/Sheets/Slides/Forms scopes beyond `drive`.

## Decision

Ship a single expanded consent set (drive + documents + spreadsheets + presentations + forms.body + forms.responses.readonly). Keep full `drive` for existing tools.

## Alternatives Considered

- Progressive/per-tool scopes — deferred (YAGNI)
- Replace `drive` with `drive.file` — rejected (would break existing tools)

## Consequences

**Breaking:** operators must re-consent. Documented in README and Connect flows (`prompt=consent`).

## Trade-offs

Broader consent surface vs simpler operations.

## Risks

Google verification burden for production SaaS — personal/dev use first.
