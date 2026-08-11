"""
Google Sheets API wrapper.
"""

from typing import Any, List, Optional, Tuple

from googleapiclient.errors import HttpError

from app.auth.clients import build_sheets_service
from app.core.exceptions import GoogleWorkspaceError, normalize_google_error
from app.services.drive_service import DriveService

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

    def list_tabs(self, spreadsheet_id: str) -> List[dict]:
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

    def read_range(self, spreadsheet_id: str, range_a1: str) -> List[List[Any]]:
        if not range_a1:
            raise GoogleWorkspaceError(
                "range is required (A1 notation)",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_a1)
                .execute()
            )
            return result.get("values", [])
        except HttpError as e:
            raise normalize_google_error(e)

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
