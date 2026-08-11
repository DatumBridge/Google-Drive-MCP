# ADR-0001 — Shared Auth Factory

## Context

Drive-only credential loading lived inside `drive_service.py` and was duplicated in OAuth routes/scripts.

## Decision

Extract `app/auth/` with a single `SCOPES` constant, `get_credentials()`, and per-product `build_*_service()` helpers.

## Alternatives Considered

- Copy credential loading into each service — rejected (drift risk)
- Env-only tokens — rejected (breaks per-call contract)

## Consequences

All services and OAuth entrypoints share one scope list. Re-consent is coordinated.

## Trade-offs

Slightly more modules; clearer SRP.

## Risks

Import cycles if services import tools — avoided by dependency direction tools → services → auth.
