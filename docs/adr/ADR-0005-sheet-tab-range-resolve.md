# ADR-0005 — Resolve missing Google Sheet tab names in A1 range

## Context

Catalog `read_sheet_range` stages often keep a static A1 range from the process
contract (for example `Budget_2026!A1:Z200`). After Excel → Google Sheets
convert, the live tab is usually `Sheet1` or `Budget 2026`. The Sheets API then
returns HTTP 400 `Unable to parse range`. That is not a bad spreadsheet id and
must not be treated as a generic `VALIDATION_ERROR`.

## Decision

1. Quote sheet titles in A1 (`'Budget 2026'!A1:Z200`) when the unquoted form fails.
2. On `Unable to parse range`, list tabs and remap **only the tab** when the match is unique:
   - exact, case-insensitive, or underscore-vs-space match
   - unique tab whose title has a **budget / ngân sách word** (not a substring such as `budgeting`)
   - **exactly one tab** only when that tab is a convert default (`Sheet1`, `Sheet2`, `Trang tính1`, …)
3. Keep the authored cell bounds (`A1:Z200`). Never invent a new cell range. A tab-only string such as `Budget_2026` (no `!`) is not rewritten as `'Sheet1'!Budget_2026`.
4. If several tabs exist and none uniquely match, or the only tab is unrelated (`Payroll`), fail closed with `INVALID_RANGE` and list the real titles plus the original Google message.
5. After remap, non-parse HTTP errors stay classified (`RATE_LIMIT`, `PERMISSION_DENIED`, …). Success responses include additive `resolved_range`.

## Alternatives Considered

- Always require operators to edit `range` after convert — rejected; convert
  routinely renames the first tab to `Sheet1`.
- Read the first 200 columns of every tab — rejected; wrong SoR and extra cost.
- Invent a default range such as `Sheet1!A1:Z1000` when `range` is unbound —
  rejected; cell bounds stay a process contract (BR-MCP-PARAM-2).

## Consequences

`budget_sheet_lookup` can read a converted workbook whose tab is `Sheet1` while
the stage still says `Budget_2026!A1:Z200`. A one-tab `Payroll` workbook still
fails closed. Ambiguous workbooks still fail closed.

## Trade-offs

One extra `spreadsheets.get` (list tabs) only after a parse failure. Successful
reads stay a single `values.get`.

## Risks

A convert-default `Sheet1` that is not the budget sheet could still be read under a
`Budget_2026!…` label. Operators with multi-tab budgets must bind the real tab
name. `resolved_range` discloses the live A1 used.
