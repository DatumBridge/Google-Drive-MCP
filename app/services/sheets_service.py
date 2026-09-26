"""
Google Sheets API wrapper.
"""

import re
from typing import Any, List, Optional, Tuple

from googleapiclient.errors import HttpError

from app.auth.clients import build_sheets_service
from app.core.exceptions import (
    GoogleWorkspaceError,
    is_unparseable_sheet_range_error,
    normalize_google_error,
)
from app.services.drive_service import DriveService

NATIVE_GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
OFFICE_SPREADSHEET_MIMES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.ms-excel.sheet.macroenabled.12",
        "application/vnd.oasis.opendocument.spreadsheet",
    }
)
OFFICE_FILE_NOT_SUPPORTED_MESSAGE = (
    "This Drive file is a Microsoft Excel/Office workbook, not a native Google Sheet. "
    "The Sheets API cannot read .xlsx/.xls/.ods file ids. In Google Drive, open the file "
    "and choose Open with → Google Sheets (or File → Save as Google Sheets). Then bind "
    "read_sheet_range.spreadsheet_id to the new Google Sheet id. Convert once; do not "
    "reconnect Integrations."
)


def _is_office_spreadsheet_mime(mime: str, name: str = "") -> bool:
    m = (mime or "").strip().lower()
    if m in OFFICE_SPREADSHEET_MIMES:
        return True
    if "openxmlformats" in m and "sheet" in m:
        return True
    n = (name or "").strip().lower()
    return n.endswith((".xlsx", ".xlsm", ".xls", ".ods"))


EXPORT_MIME_MAP = {
    "csv": "text/csv",
    "text/csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    "pdf": "application/pdf",
    "application/pdf": "application/pdf",
}

MAX_EXPORT_BYTES = 25 * 1024 * 1024
MAX_CELLS = 50_000
_A1_CELLS_RE = re.compile(r"^[A-Za-z]{1,3}\d+(?::[A-Za-z]{1,3}\d+)?$")
_CONVERT_DEFAULT_TAB_RE = re.compile(
    r"^(Sheet\d*|Trang tính\d*|Hoja\d*|Feuille\d*)$",
    re.IGNORECASE,
)
_BUDGET_WORD_RE = re.compile(r"\bbudget\b", re.IGNORECASE)


def looks_like_a1_cells(text: str) -> bool:
    return bool(_A1_CELLS_RE.match((text or "").replace("$", "").strip()))


def _has_budget_token(text: str) -> bool:
    lowered = (text or "").lower().replace("_", " ")
    if "ngân sách" in lowered or "ngan sach" in lowered:
        return True
    return bool(_BUDGET_WORD_RE.search(lowered))


def split_a1_range(range_a1: str) -> Tuple[Optional[str], str]:
    text = (range_a1 or "").strip()
    if not text:
        return None, ""
    if text.startswith("'"):
        marker = text.find("'!", 1)
        if marker == -1:
            return text.strip("'"), ""
        title = text[1:marker].replace("''", "'")
        return title, text[marker + 2 :].strip()
    if "!" in text:
        title, cells = text.split("!", 1)
        return title.strip().strip("'"), cells.strip()
    return None, text


def quote_a1_range(sheet_title: str, cells: str) -> str:
    escaped = (sheet_title or "").replace("'", "''")
    bounds = (cells or "").strip()
    if not bounds:
        return f"'{escaped}'"
    return f"'{escaped}'!{bounds}"


def pick_sheet_title(requested: Optional[str], titles: List[str]) -> Optional[str]:
    clean = [t for t in titles if isinstance(t, str) and t.strip()]
    if not clean:
        return None
    if requested:
        for title in clean:
            if title == requested:
                return title
        lowered = requested.lower()
        case_hits = [t for t in clean if t.lower() == lowered]
        if len(case_hits) == 1:
            return case_hits[0]
        normalized = lowered.replace("_", " ")
        space_hits = [t for t in clean if t.lower().replace("_", " ") == normalized]
        if len(space_hits) == 1:
            return space_hits[0]
        if _has_budget_token(requested):
            budget_hits = [t for t in clean if _has_budget_token(t)]
            if len(budget_hits) == 1:
                return budget_hits[0]
    if len(clean) == 1 and _CONVERT_DEFAULT_TAB_RE.match(clean[0].strip()):
        return clean[0]
    return None


def _invalid_range_error(
    requested: str,
    titles: List[str],
    original: Optional[Exception] = None,
) -> GoogleWorkspaceError:
    tab_list = ", ".join(repr(t) for t in titles) if titles else "(none)"
    original_text = str(original).strip().split("\n", 1)[0] if original else ""
    suffix = f" Original: {original_text}" if original_text else ""
    return GoogleWorkspaceError(
        message=(
            f"Unable to parse range {requested!r}. That tab is not on this Google Sheet. "
            f"Tabs: {tab_list}. Bind range to an existing tab "
            f"(for example 'Sheet1'!A1:Z200).{suffix}"
        ),
        error_code="INVALID_RANGE",
        retryable=False,
        original_error=original,
    )


class SheetsService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._sheets = build_sheets_service(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )
        self._drive = DriveService(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    def create_spreadsheet(
        self,
        title: str = "Untitled spreadsheet",
        sheet_titles: Optional[List[str]] = None,
        parent_folder_id: Optional[str] = None,
    ) -> dict:
        try:
            body: dict = {"properties": {"title": title}}
            if sheet_titles:
                body["sheets"] = [
                    {"properties": {"title": name, "index": i}}
                    for i, name in enumerate(sheet_titles)
                ]
            spreadsheet = self._sheets.spreadsheets().create(body=body).execute()
        except HttpError as e:
            raise normalize_google_error(e)
        spreadsheet_id = spreadsheet["spreadsheetId"]
        parent_applied, parent_error = self._drive.apply_parent(
            spreadsheet_id, parent_folder_id
        )
        return {
            "spreadsheet_id": spreadsheet_id,
            "title": spreadsheet.get("properties", {}).get("title", title),
            "spreadsheet_url": spreadsheet.get("spreadsheetUrl"),
            "parent_applied": parent_applied,
            "parent_error": parent_error,
        }

    def _ensure_native_google_sheet(self, spreadsheet_id: str) -> None:
        """Sheets API only works on native Google Sheets, not uploaded Excel files."""
        meta = self._drive.get_metadata(spreadsheet_id)
        mime = (getattr(meta, "mime_type", None) or "").strip().lower()
        name = getattr(meta, "name", None) or spreadsheet_id
        if getattr(meta, "trashed", False):
            raise GoogleWorkspaceError(
                f"Drive file {name!r} is in Trash. Empty Trash or restore it, then bind "
                "read_sheet_range.spreadsheet_id to a live native Google Sheet id "
                "(not the deleted .xlsx). Catalog List Run uses the saved stage parameter, "
                "not canvas label edits.",
                error_code="FILE_IN_TRASH",
                retryable=False,
            )
        if mime == NATIVE_GOOGLE_SHEET_MIME:
            return
        if _is_office_spreadsheet_mime(mime, str(name)):
            raise GoogleWorkspaceError(
                OFFICE_FILE_NOT_SUPPORTED_MESSAGE,
                error_code="OFFICE_FILE_NOT_SUPPORTED",
                retryable=False,
            )
        if mime:
            raise GoogleWorkspaceError(
                f"Drive file {name!r} is {mime}, not a native Google Sheet "
                f"({NATIVE_GOOGLE_SHEET_MIME}). Convert it in Drive (Open with → "
                "Google Sheets) and use that file id as spreadsheet_id.",
                error_code="OFFICE_FILE_NOT_SUPPORTED",
                retryable=False,
            )

    def list_tabs(self, spreadsheet_id: str) -> List[dict]:
        self._ensure_native_google_sheet(spreadsheet_id)
        try:
            spreadsheet = (
                self._sheets.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
                .execute()
            )
            tabs = []
            for sheet in spreadsheet.get("sheets", []):
                props = sheet.get("properties", {})
                tabs.append(
                    {
                        "sheet_id": props.get("sheetId"),
                        "title": props.get("title"),
                        "index": props.get("index", 0),
                    }
                )
            return tabs
        except HttpError as e:
            raise normalize_google_error(e)

    def _values_get(self, spreadsheet_id: str, range_a1: str) -> List[List[Any]]:
        result = (
            self._sheets.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_a1)
            .execute()
        )
        return result.get("values", [])

    def _read_values_with_tab_resolve(
        self, spreadsheet_id: str, range_a1: str
    ) -> Tuple[List[List[Any]], str]:
        """Fetch A1 values; remap a missing tab, never invent cell bounds."""
        title, cells = split_a1_range(range_a1)
        attempts = [range_a1]
        if title:
            quoted = quote_a1_range(title, cells)
            if quoted not in attempts:
                attempts.append(quoted)
        last_err: Optional[Exception] = None
        for attempt in attempts:
            try:
                return self._values_get(spreadsheet_id, attempt), attempt
            except HttpError as exc:
                last_err = exc
                if not is_unparseable_sheet_range_error(exc):
                    raise normalize_google_error(exc) from exc
        tabs = self.list_tabs(spreadsheet_id)
        titles = [str(t.get("title") or "") for t in tabs]
        if cells and not looks_like_a1_cells(cells):
            raise _invalid_range_error(range_a1, titles, last_err)
        chosen = pick_sheet_title(title, titles)
        if chosen:
            resolved = quote_a1_range(chosen, cells)
            if resolved not in attempts:
                try:
                    return self._values_get(spreadsheet_id, resolved), resolved
                except HttpError as exc:
                    if is_unparseable_sheet_range_error(exc):
                        raise _invalid_range_error(range_a1, titles, exc) from exc
                    raise normalize_google_error(exc) from exc
        raise _invalid_range_error(range_a1, titles, last_err)

    def read_range_resolved(
        self, spreadsheet_id: str, range_a1: str
    ) -> Tuple[List[List[Any]], str]:
        if not range_a1:
            raise GoogleWorkspaceError(
                "range is required (A1 notation)",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        self._ensure_native_google_sheet(spreadsheet_id)
        return self._read_values_with_tab_resolve(spreadsheet_id, range_a1)

    def read_range(self, spreadsheet_id: str, range_a1: str) -> List[List[Any]]:
        values, _resolved = self.read_range_resolved(spreadsheet_id, range_a1)
        return values

    def update_range(
        self,
        spreadsheet_id: str,
        range_a1: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        self._validate_values(values)
        if value_input_option not in ("RAW", "USER_ENTERED"):
            raise GoogleWorkspaceError(
                "value_input_option must be RAW or USER_ENTERED",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        self._ensure_native_google_sheet(spreadsheet_id)
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_a1,
                    valueInputOption=value_input_option,
                    body={"values": values},
                )
                .execute()
            )
            return {
                "updated_range": result.get("updatedRange"),
                "updated_rows": result.get("updatedRows"),
                "updated_columns": result.get("updatedColumns"),
                "updated_cells": result.get("updatedCells"),
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def append_rows(
        self,
        spreadsheet_id: str,
        range_a1: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        self._validate_values(values)
        if value_input_option not in ("RAW", "USER_ENTERED"):
            raise GoogleWorkspaceError(
                "value_input_option must be RAW or USER_ENTERED",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        self._ensure_native_google_sheet(spreadsheet_id)
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_a1,
                    valueInputOption=value_input_option,
                    insertDataOption="INSERT_ROWS",
                    body={"values": values},
                )
                .execute()
            )
            updates = result.get("updates", {})
            return {
                "updated_range": updates.get("updatedRange"),
                "updated_rows": updates.get("updatedRows"),
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def clear_range(self, spreadsheet_id: str, range_a1: str) -> str:
        if not range_a1:
            raise GoogleWorkspaceError(
                "range is required (A1 notation)",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        self._ensure_native_google_sheet(spreadsheet_id)
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .clear(spreadsheetId=spreadsheet_id, range=range_a1, body={})
                .execute()
            )
            return result.get("clearedRange", range_a1)
        except HttpError as e:
            raise normalize_google_error(e)

    def add_tab(self, spreadsheet_id: str, title: str) -> dict:
        if not title:
            raise GoogleWorkspaceError(
                "title is required",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        self._ensure_native_google_sheet(spreadsheet_id)
        try:
            result = (
                self._sheets.spreadsheets()
                .batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        "requests": [
                            {"addSheet": {"properties": {"title": title}}}
                        ]
                    },
                )
                .execute()
            )
            props = (
                result.get("replies", [{}])[0]
                .get("addSheet", {})
                .get("properties", {})
            )
            return {"sheet_id": props.get("sheetId"), "title": props.get("title", title)}
        except HttpError as e:
            raise normalize_google_error(e)

    def export_spreadsheet(
        self, spreadsheet_id: str, export_format: str = "xlsx"
    ) -> Tuple[bytes, str]:
        mime = EXPORT_MIME_MAP.get(export_format)
        if not mime:
            raise GoogleWorkspaceError(
                f"Unsupported export_format: {export_format}. "
                f"Supported: csv, xlsx, pdf",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        content = self._drive.export_file(spreadsheet_id, mime)
        if len(content) > MAX_EXPORT_BYTES:
            raise GoogleWorkspaceError(
                f"Export exceeds {MAX_EXPORT_BYTES} bytes limit",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        return content, mime

    @staticmethod
    def _validate_values(values: List[List[Any]]) -> None:
        if not isinstance(values, list) or not values:
            raise GoogleWorkspaceError(
                "values must be a non-empty 2D array",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        cell_count = 0
        for row in values:
            if not isinstance(row, list):
                raise GoogleWorkspaceError(
                    "each row in values must be a list",
                    error_code="VALIDATION_ERROR",
                    retryable=False,
                )
            cell_count += len(row)
        if cell_count > MAX_CELLS:
            raise GoogleWorkspaceError(
                f"values exceed {MAX_CELLS} cells limit",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
