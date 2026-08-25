"""Contract tests for create-with-parent soft-fail (ADR-0004) and tool registration."""

from unittest.mock import MagicMock

from fastmcp import FastMCP

from app.core.exceptions import DrivePermissionError, GoogleWorkspaceError, normalize_google_error
from app.services.diagram_service import DiagramService
from app.services.docs_service import DocsService
from app.services.drive_service import DriveService
from app.services.forms_service import FormsService
from app.services.sheets_service import SheetsService
from app.services.slides_service import SlidesService
from app.tools import register_all
from scripts.test_mcp_tools import EXPECTED_TOOLS


def test_apply_parent_no_parent_returns_false():
    drive = DriveService.__new__(DriveService)
    drive._service = MagicMock()
    applied, err = drive.apply_parent("file-1", None)
    assert applied is False
    assert err is None


def test_apply_parent_success():
    drive = DriveService.__new__(DriveService)
    drive._service = MagicMock()
    drive.move_file = MagicMock(return_value={"id": "file-1", "parents": ["folder-1"]})
    applied, err = drive.apply_parent("file-1", "folder-1")
    assert applied is True
    assert err is None
    drive.move_file.assert_called_once_with(
        file_id="file-1", new_parent_folder_id="folder-1"
    )


def test_apply_parent_soft_fails_with_error_dict():
    drive = DriveService.__new__(DriveService)
    drive._service = MagicMock()
    drive.move_file = MagicMock(side_effect=DrivePermissionError("Permission denied"))
    applied, err = drive.apply_parent("file-1", "folder-1")
    assert applied is False
    assert err is not None
    assert err["error_code"] == "PERMISSION_DENIED"
    assert err["retryable"] is False


def _parent_fail():
    return (
        False,
        {
            "error_code": "PERMISSION_DENIED",
            "error_message": "Permission denied",
            "retryable": False,
            "original_provider_error": None,
        },
    )


def test_create_document_keeps_id_when_parent_move_fails():
    svc = DocsService.__new__(DocsService)
    docs_api = MagicMock()
    docs_api.documents().create().execute.return_value = {
        "documentId": "doc-123",
        "title": "Test Doc",
    }
    svc._docs = docs_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = _parent_fail()
    meta = MagicMock()
    meta.web_view_link = "https://docs.google.com/document/d/doc-123"
    svc._drive.get_metadata.return_value = meta

    result = svc.create_document(title="Test Doc", parent_folder_id="folder-bad")
    assert result["document_id"] == "doc-123"
    assert result["parent_applied"] is False
    assert result["parent_error"]["error_code"] == "PERMISSION_DENIED"
    assert result["web_view_link"]


def test_create_document_keeps_id_when_metadata_fails():
    svc = DocsService.__new__(DocsService)
    docs_api = MagicMock()
    docs_api.documents().create().execute.return_value = {
        "documentId": "doc-meta",
        "title": "Meta Fail",
    }
    svc._docs = docs_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = (False, None)
    svc._drive.get_metadata.side_effect = DrivePermissionError("Permission denied")

    result = svc.create_document(title="Meta Fail")
    assert result["document_id"] == "doc-meta"
    assert result["web_view_link"] is None
    assert result["parent_applied"] is False


def test_create_document_no_parent():
    svc = DocsService.__new__(DocsService)
    docs_api = MagicMock()
    docs_api.documents().create().execute.return_value = {
        "documentId": "doc-456",
        "title": "No Parent",
    }
    svc._docs = docs_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = (False, None)
    meta = MagicMock()
    meta.web_view_link = "https://example.com/doc-456"
    svc._drive.get_metadata.return_value = meta

    result = svc.create_document(title="No Parent")
    assert result["document_id"] == "doc-456"
    assert result["parent_applied"] is False
    assert result["parent_error"] is None


def test_create_spreadsheet_keeps_id_when_parent_move_fails():
    svc = SheetsService.__new__(SheetsService)
    sheets_api = MagicMock()
    sheets_api.spreadsheets().create().execute.return_value = {
        "spreadsheetId": "sheet-1",
        "properties": {"title": "Budget"},
        "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet-1",
    }
    svc._sheets = sheets_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = _parent_fail()

    result = svc.create_spreadsheet(title="Budget", parent_folder_id="folder-bad")
    assert result["spreadsheet_id"] == "sheet-1"
    assert result["parent_applied"] is False
    assert result["parent_error"]["error_code"] == "PERMISSION_DENIED"


def test_create_presentation_keeps_id_when_parent_move_fails():
    svc = SlidesService.__new__(SlidesService)
    slides_api = MagicMock()
    slides_api.presentations().create().execute.return_value = {
        "presentationId": "pres-1",
        "title": "Deck",
    }
    svc._slides = slides_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = _parent_fail()
    meta = MagicMock()
    meta.web_view_link = "https://docs.google.com/presentation/d/pres-1"
    svc._drive.get_metadata.return_value = meta

    result = svc.create_presentation(title="Deck", parent_folder_id="folder-bad")
    assert result["presentation_id"] == "pres-1"
    assert result["parent_applied"] is False
    assert result["parent_error"]["error_code"] == "PERMISSION_DENIED"


def test_create_form_keeps_id_when_parent_move_fails():
    svc = FormsService.__new__(FormsService)
    forms_api = MagicMock()
    forms_api.forms().create().execute.return_value = {
        "formId": "form-1",
        "info": {"title": "Survey"},
        "responderUri": "https://forms.gle/example",
    }
    svc._forms = forms_api
    svc._drive = MagicMock()
    svc._drive.apply_parent.return_value = _parent_fail()

    result = svc.create_form(title="Survey", parent_folder_id="folder-bad")
    assert result["form_id"] == "form-1"
    assert result["parent_applied"] is False
    assert result["parent_error"]["error_code"] == "PERMISSION_DENIED"


def test_create_diagram_parent_applied_only_when_parent_set():
    svc = DiagramService.__new__(DiagramService)
    svc._drive = MagicMock()
    svc._drive.upload_file.return_value = {
        "id": "diag-1",
        "name": "x.drawio",
        "webViewLink": "https://drive.google.com/file/d/diag-1",
    }
    with_parent = svc.create_diagram(name="x", parent_folder_id="folder-1")
    assert with_parent["parent_applied"] is True
    assert with_parent["parent_error"] is None

    without = svc.create_diagram(name="y")
    assert without["parent_applied"] is False


def test_normalize_google_error_uses_status_code():
    class Resp:
        status = 403

    class FakeHttpError(Exception):
        def __init__(self):
            self.resp = Resp()
            super().__init__("ignored message without status digits")

    err = normalize_google_error(FakeHttpError())
    assert isinstance(err, GoogleWorkspaceError)
    assert err.error_code == "PERMISSION_DENIED"


def test_normalize_google_error_sheets_api_not_enabled():
    class Resp:
        status = 403

    class FakeHttpError(Exception):
        def __init__(self):
            self.resp = Resp()
            super().__init__(
                'HttpError 403 when requesting https://sheets.googleapis.com/v4/spreadsheets/abc/values/A1 '
                'returned "Google Sheets API has not been used in project 000000000001 before or it is disabled. '
                "Enable it by visiting https://console.developers.google.com/apis/api/sheets.googleapis.com/"
                'overview?project=000000000001 then retry.". Details: "[{reason: SERVICE_DISABLED}]"'
            )

    err = normalize_google_error(FakeHttpError())
    assert err.error_code == "API_NOT_ENABLED"
    assert err.retryable is True
    assert "Google Sheets API" in err.message
    assert "sheets.googleapis.com" in err.message
    assert "not a Drive sharing ACL" in err.message


def test_normalize_google_error_office_xlsx_not_supported():
    class Resp:
        status = 400

    class FakeHttpError(Exception):
        def __init__(self):
            self.resp = Resp()
            super().__init__(
                'HttpError 400 when requesting https://sheets.googleapis.com/v4/spreadsheets/abc/values/A1 '
                'returned "This operation is not supported for this document. '
                'The document must not be an Office file."'
            )

    err = normalize_google_error(FakeHttpError())
    assert err.error_code == "OFFICE_FILE_NOT_SUPPORTED"
    assert err.retryable is False
    assert "Google Sheet" in err.message


def test_normalize_google_error_invalid_q_is_not_auth_error():
    class Resp:
        status = 400

    class FakeHttpError(Exception):
        def __init__(self):
            self.resp = Resp()
            super().__init__(
                "<HttpError 400 when requesting "
                "https://www.googleapis.com/drive/v3/files?q=%27root%27+in+parents+"
                "and+mua+ph%E1%BA%A7n+m%E1%BB%81m+CRM+zoho&pageSize=10&pageToken=&"
                "fields=nextPageToken%2C+files%28id%2C+name%29&alt=json returned "
                "\"Invalid Value\". Details: \"[{'message': 'Invalid Value', "
                "'domain': 'global', 'reason': 'invalid', 'location': 'q', "
                "'locationType': 'parameter'}]\">"
            )

    err = normalize_google_error(FakeHttpError())
    assert err.error_code == "INVALID_QUERY"
    assert "Invalid Value" in err.message
    assert "name contains" in err.message


def test_coerce_drive_list_query_wraps_natural_language():
    from app.services.drive_service import coerce_drive_list_query

    assert coerce_drive_list_query("mua phần mềm CRM zoho") == (
        "name contains 'mua phần mềm CRM zoho'"
    )
    assert (
        coerce_drive_list_query("mimeType='application/vnd.google-apps.spreadsheet'")
        == "mimeType='application/vnd.google-apps.spreadsheet'"
    )
    assert coerce_drive_list_query("name contains 'budget'") == "name contains 'budget'"


def test_read_range_rejects_xlsx_office_file():
    from app.schemas.drive import FileMetadata

    svc = SheetsService.__new__(SheetsService)
    svc._sheets = MagicMock()
    svc._drive = MagicMock()
    svc._drive.get_metadata.return_value = FileMetadata(
        id="xlsx-1",
        name="budget_2026.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    try:
        svc.read_range("xlsx-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected OFFICE_FILE_NOT_SUPPORTED")
    except GoogleWorkspaceError as err:
        assert err.error_code == "OFFICE_FILE_NOT_SUPPORTED"
        assert "Excel" in err.message or "Office" in err.message
    svc._sheets.spreadsheets().values().get.assert_not_called()


def test_read_range_rejects_trashed_file():
    from app.schemas.drive import FileMetadata

    svc = SheetsService.__new__(SheetsService)
    svc._sheets = MagicMock()
    svc._drive = MagicMock()
    svc._drive.get_metadata.return_value = FileMetadata(
        id="xlsx-1",
        name="budget_2026.xlsx",
        mime_type="application/vnd.google-apps.spreadsheet",
        trashed=True,
    )
    try:
        svc.read_range("xlsx-1", "Budget_2026!A1:Z200")
        raise AssertionError("expected FILE_IN_TRASH")
    except GoogleWorkspaceError as err:
        assert err.error_code == "FILE_IN_TRASH"
    svc._sheets.spreadsheets().values().get.assert_not_called()


def test_list_files_query_excludes_trash():
    drive = DriveService.__new__(DriveService)
    listed = MagicMock()
    listed.execute.return_value = {"files": []}
    files_api = MagicMock()
    files_api.list.return_value = listed
    drive._service = MagicMock()
    drive._service.files.return_value = files_api
    drive.list_files(folder_id=None, query="name contains 'budget'")
    kwargs = files_api.list.call_args.kwargs
    assert "trashed = false" in (kwargs.get("q") or "")
    assert "name contains 'budget'" in (kwargs.get("q") or "")


def test_list_files_wraps_natural_language_query():
    drive = DriveService.__new__(DriveService)
    listed = MagicMock()
    listed.execute.return_value = {"files": []}
    files_api = MagicMock()
    files_api.list.return_value = listed
    drive._service = MagicMock()
    drive._service.files.return_value = files_api
    drive.list_files(folder_id=None, query="mua phần mềm CRM zoho")
    q = files_api.list.call_args.kwargs.get("q") or ""
    assert "name contains 'mua phần mềm CRM zoho'" in q
    assert "trashed = false" in q


def test_all_expected_tools_registered():
    mcp = FastMCP("google-drive")
    register_all(mcp)
    names = set(mcp._tool_manager._tools.keys())
    assert names == EXPECTED_TOOLS
    assert len(names) == 39


def test_delete_file_requires_confirm():
    from unittest.mock import patch

    from app.tools import drive_tools

    mcp = FastMCP("t")
    drive_tools.register(mcp)
    delete_fn = mcp._tool_manager._tools["delete_file"].fn
    with patch("app.tools.drive_tools.get_drive") as get_drive:
        result = delete_fn(
            file_id="file-x",
            confirm=False,
            credentials_path="/tmp/token.json",
            credentials_json=None,
        )
        assert result.success is False
        assert result.error["error_code"] == "CONFIRMATION_REQUIRED"
        get_drive.assert_not_called()


def test_forms_include_answers_default_omits_answers():
    svc = FormsService.__new__(FormsService)
    forms_api = MagicMock()
    forms_api.forms().responses().list().execute.return_value = {
        "responses": [
            {
                "responseId": "r1",
                "createTime": "2026-01-01T00:00:00Z",
                "lastSubmittedTime": "2026-01-01T00:00:00Z",
                "answers": {"q1": {"textAnswers": {"answers": [{"value": "secret"}]}}},
            }
        ]
    }
    forms_api.forms().responses().get().execute.return_value = {
        "responseId": "r1",
        "createTime": "2026-01-01T00:00:00Z",
        "lastSubmittedTime": "2026-01-01T00:00:00Z",
        "answers": {"q1": {"textAnswers": {"answers": [{"value": "secret"}]}}},
    }
    svc._forms = forms_api
    svc._simplify_answers = MagicMock(return_value={"q1": ["secret"]})

    listed = svc.list_responses("form-1")  # default include_answers=False
    assert "answers" not in listed["responses"][0]

    listed_on = svc.list_responses("form-1", include_answers=True)
    assert listed_on["responses"][0]["answers"] == {"q1": ["secret"]}

    detail = svc.get_response("form-1", "r1")
    assert "answers" not in detail
    detail_on = svc.get_response("form-1", "r1", include_answers=True)
    assert detail_on["answers"] == {"q1": ["secret"]}


def test_forms_tool_defaults_include_answers_false():
    from app.tools import forms_tools
    import inspect

    mcp = FastMCP("t")
    forms_tools.register(mcp)
    list_fn = mcp._tool_manager._tools["list_form_responses"].fn
    list_default = inspect.signature(list_fn).parameters["include_answers"].default
    assert getattr(list_default, "default", list_default) is False
    get_fn = mcp._tool_manager._tools["get_form_response"].fn
    get_default = inspect.signature(get_fn).parameters["include_answers"].default
    assert getattr(get_default, "default", get_default) is False


def test_delete_file_tool_confirm_default_false():
    from app.tools import drive_tools
    import inspect

    mcp = FastMCP("t")
    drive_tools.register(mcp)
    delete_fn = mcp._tool_manager._tools["delete_file"].fn
    confirm_default = inspect.signature(delete_fn).parameters["confirm"].default
    assert getattr(confirm_default, "default", confirm_default) is False
