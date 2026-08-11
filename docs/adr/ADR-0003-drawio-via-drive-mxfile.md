# ADR-0003 — draw.io via Drive mxfile

## Context

There is no Google Draw.io / diagrams.net content API.

## Decision

Treat diagrams as Drive files (`application/vnd.jgraph.mxfile` / `.drawio`). Provide create/list/read/update/export-XML tools only.

## Alternatives Considered

- Headless diagrams.net export service — out of scope
- Mermaid→draw.io converter — deferred

## Consequences

Agents edit XML; PNG/PDF conversion is client-side (diagrams.net).

## Trade-offs

No visual fidelity guarantees; simple and auditable.

## Risks

MIME/name variance — mitigated with heuristic list query.
