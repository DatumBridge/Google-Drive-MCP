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
