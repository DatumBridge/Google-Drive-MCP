# ADR-0004 — Create-with-Parent Strategy

## Context

Docs/Sheets/Slides/Forms create APIs do not always accept Drive parents the same way as Drive `files.create`.

## Decision

1. Create via product API
2. If `parent_folder_id` set, call `DriveService.apply_parent` (move)
3. Return `parent_applied` boolean and optional `parent_error`

**Soft-fail contract (required):** if product create succeeds and the parent move fails, the create response remains `success=true`, includes the created resource id / URLs, sets `parent_applied=false`, and surfaces `parent_error` with the standardized error envelope. Agents recover by calling `move_file`. Do not hard-fail create without returning the resource id (that leaves agent-invisible orphans).

Diagrams set parents at Drive create time (single step). On successful upload with a parent, `parent_applied=true`; if omitted, `parent_applied=false`.

## Alternatives Considered

- Drive create + conversion — more fragile for Forms
- Silent orphan on move failure — rejected
- Hard-fail create when move fails — rejected (hides resource id)

## Consequences

Agents can detect parent placement failures and call `move_file`.

## Trade-offs

Two API calls for Workspace creates with parent.

## Risks

Shared Drives unsupported in this PR (same as prior Drive tools).
