"""read_sheet_range A1 tab remap (ADR-0005)."""

from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from app.core.exceptions import GoogleWorkspaceError, DriveRateLimitError, DrivePermissionError
from app.services.sheets_service import SheetsService, looks_like_a1_cells, pick_sheet_title


def _http_error(status: int, message: str) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Error"
    return HttpError(resp, message.encode())


def _unparseable(a1: str) -> HttpError:
    return _http_error(400, f'Unable to parse range: {a1}')


def _native_sheet_service(tabs: list[str]):
    from app.schemas.drive import FileMetadata

    svc = SheetsService.__new__(SheetsService)
    svc._drive = MagicMock()
    svc._drive.get_metadata.return_value = FileMetadata(
        id="sheet-1",
        name="Budget 2026",
        mime_type="application/vnd.google-apps.spreadsheet",
    )
    ss = MagicMock()
    svc._sheets = MagicMock()
    svc._sheets.spreadsheets.return_value = ss
    ss.get.return_value.execute.return_value = {
        "sheets": [
            {"properties": {"sheetId": i, "title": title, "index": i}}
            for i, title in enumerate(tabs)
        ]
    }
    return svc, ss


def test_looks_like_a1_cells():
    assert looks_like_a1_cells("A1:Z200")
    assert looks_like_a1_cells("AA10")
    assert not looks_like_a1_cells("Budget_2026")
    assert not looks_like_a1_cells("")


def test_read_range_underscore_vs_space_keeps_cells():
    svc, ss = _native_sheet_service(["Budget 2026", "Notes"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        if range in ("Budget_2026!A1:Z200", "'Budget_2026'!A1:Z200"):
            req.execute.side_effect = _unparseable(range)
        elif range == "'Budget 2026'!A1:Z200":
            req.execute.return_value = {"values": [["ok"]]}
        else:
            raise AssertionError(f"unexpected range {range!r}")
        return req

    ss.values.return_value.get.side_effect = values_get
    values, resolved = svc.read_range_resolved("sheet-1", "Budget_2026!A1:Z200")
    assert values == [["ok"]]
    assert resolved == "'Budget 2026'!A1:Z200"


def test_read_range_quoted_missing_tab_uses_sheet1():
    svc, ss = _native_sheet_service(["Sheet1"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        if range in ("'Budget_2026'!A1:Z200",):
            req.execute.side_effect = _unparseable(range)
        elif range == "'Sheet1'!A1:Z200":
            req.execute.return_value = {"values": [["ok"]]}
        else:
            raise AssertionError(f"unexpected range {range!r}")
        return req

    ss.values.return_value.get.side_effect = values_get
    values, resolved = svc.read_range_resolved("sheet-1", "'Budget_2026'!A1:Z200")
    assert values == [["ok"]]
    assert resolved == "'Sheet1'!A1:Z200"


def test_read_range_unique_ngan_sach_among_tabs():
    svc, ss = _native_sheet_service(["Q1", "Budget 2026"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        if "Budget_2026" in range or "Ngân" in range:
            req.execute.side_effect = _unparseable(range)
        elif range == "'Budget 2026'!A1:Z200":
            req.execute.return_value = {"values": [["ok"]]}
        else:
            raise AssertionError(f"unexpected range {range!r}")
        return req

    ss.values.return_value.get.side_effect = values_get
    values, resolved = svc.read_range_resolved("sheet-1", "Ngân sách!A1:Z200")
    assert values == [["ok"]]
    assert resolved == "'Budget 2026'!A1:Z200"


def test_read_range_two_budget_tabs_fail_closed():
    svc, ss = _native_sheet_service(["Budget Q1", "Budget Q2"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        req.execute.side_effect = _unparseable(range)
        return req

    ss.values.return_value.get.side_effect = values_get
    try:
        svc.read_range("sheet-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected INVALID_RANGE")
    except GoogleWorkspaceError as err:
        assert err.error_code == "INVALID_RANGE"
        assert "Budget Q1" in err.message
        assert "Budget Q2" in err.message


def test_read_range_payroll_singleton_is_not_budget():
    svc, ss = _native_sheet_service(["Payroll"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        req.execute.side_effect = _unparseable(range)
        return req

    ss.values.return_value.get.side_effect = values_get
    try:
        svc.read_range("sheet-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected INVALID_RANGE")
    except GoogleWorkspaceError as err:
        assert err.error_code == "INVALID_RANGE"
        assert "Payroll" in err.message


def test_read_range_tab_name_only_does_not_invent_cells():
    svc, ss = _native_sheet_service(["Sheet1"])
    requested = []

    def values_get(*, spreadsheetId, range):
        requested.append(range)
        req = MagicMock()
        req.execute.side_effect = _unparseable(range)
        return req

    ss.values.return_value.get.side_effect = values_get
    try:
        svc.read_range("sheet-1", "Budget_2026")
        raise AssertionError("expected INVALID_RANGE")
    except GoogleWorkspaceError as err:
        assert err.error_code == "INVALID_RANGE"
    assert all(not str(r).endswith("!Budget_2026") for r in requested)


def test_read_range_resolved_429_is_rate_limit():
    svc, ss = _native_sheet_service(["Sheet1"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        if range in ("Budget_2026!A1:Z200", "'Budget_2026'!A1:Z200"):
            req.execute.side_effect = _unparseable(range)
        elif range == "'Sheet1'!A1:Z200":
            req.execute.side_effect = _http_error(429, "Rate limit exceeded")
        else:
            raise AssertionError(f"unexpected range {range!r}")
        return req

    ss.values.return_value.get.side_effect = values_get
    try:
        svc.read_range("sheet-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected RATE_LIMIT")
    except DriveRateLimitError as err:
        assert err.error_code == "RATE_LIMIT"
        assert err.retryable is True


def test_read_range_resolved_403_is_permission_denied():
    svc, ss = _native_sheet_service(["Sheet1"])

    def values_get(*, spreadsheetId, range):
        req = MagicMock()
        if range in ("Budget_2026!A1:Z200", "'Budget_2026'!A1:Z200"):
            req.execute.side_effect = _unparseable(range)
        elif range == "'Sheet1'!A1:Z200":
            req.execute.side_effect = _http_error(403, "The caller does not have permission")
        else:
            raise AssertionError(f"unexpected range {range!r}")
        return req

    ss.values.return_value.get.side_effect = values_get
    try:
        svc.read_range("sheet-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected PERMISSION_DENIED")
    except DrivePermissionError as err:
        assert err.error_code == "PERMISSION_DENIED"


def test_pick_sheet_title_two_budget_tabs():
    assert pick_sheet_title("Budget_2026", ["Budget Q1", "Budget Q2"]) is None
