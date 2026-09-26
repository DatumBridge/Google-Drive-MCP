"""Google Sheets MCP tools."""

import base64
import json
import logging
from typing import Any, List, Optional, Union

from pydantic import Field

from app.schemas.sheets import (
    AddSheetTabResponse,
    AppendSheetRowsResponse,
    ClearSheetRangeResponse,
    CreateSpreadsheetResponse,
    ExportSpreadsheetResponse,
    ListSheetTabsResponse,
    ReadSheetRangeResponse,
    SheetTabInfo,
    UpdateSheetRangeResponse,
)
from app.tools.common import (
    CREDENTIALS_REQUIRED_ERROR,
    DriveError,
    credentials_missing,
    error_dict,
    get_sheets,
)

logger = logging.getLogger(__name__)


def _parse_values(values: Union[List[List[Any]], str]) -> List[List[Any]]:
    if isinstance(values, str):
        parsed = json.loads(values)
    else:
        parsed = values
    if not isinstance(parsed, list):
        raise ValueError("values must be a 2D array")
    return parsed


def register(mcp) -> None:
    @mcp.tool()
    def create_spreadsheet(
        title: str = Field(default="Untitled spreadsheet", description="Spreadsheet title"),
        sheet_titles: Optional[List[str]] = Field(
            default=None, description="Optional initial sheet/tab titles"
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
        parent_folder_id: Optional[str] = Field(default=None, description="Optional Drive parent folder ID"),
    ) -> CreateSpreadsheetResponse:
        """Create a Google Spreadsheet. Optionally place it in a Drive folder.

        Capabilities: drive.create_spreadsheet
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return CreateSpreadsheetResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_sheets(credentials_path, credentials_json).create_spreadsheet(
                title=title, sheet_titles=sheet_titles, parent_folder_id=parent_folder_id
            )
            return CreateSpreadsheetResponse(success=True, **result)
        except DriveError as e:
            logger.error(f"create_spreadsheet failed: {e.message}")
            return CreateSpreadsheetResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def list_sheet_tabs(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ListSheetTabsResponse:
        """List sheet tabs (title + sheetId) in a spreadsheet.

        Capabilities: drive.list_sheet_tabs
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ListSheetTabsResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            tabs = get_sheets(credentials_path, credentials_json).list_tabs(spreadsheet_id)
            return ListSheetTabsResponse(
                success=True,
                spreadsheet_id=spreadsheet_id,
                tabs=[SheetTabInfo(**t) for t in tabs],
            )
        except DriveError as e:
            logger.error(f"list_sheet_tabs failed: {e.message}")
            return ListSheetTabsResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def read_sheet_range(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        range: str = Field(..., description="A1 notation range, e.g. Sheet1!A1:C10"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ReadSheetRangeResponse:
        """Read values from a spreadsheet range (A1 notation).

        Capabilities: drive.read_sheet_range
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ReadSheetRangeResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            values, resolved = get_sheets(
                credentials_path, credentials_json
            ).read_range_resolved(spreadsheet_id, range)
            return ReadSheetRangeResponse(
                success=True,
                spreadsheet_id=spreadsheet_id,
                range=range,
                resolved_range=resolved,
                values=values,
            )
        except DriveError as e:
            logger.error(f"read_sheet_range failed: {e.message}")
            return ReadSheetRangeResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def update_sheet_range(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        range: str = Field(..., description="A1 notation range to write"),
        values: Union[List[List[Any]], str] = Field(
            ..., description="2D array of values, or JSON string of 2D array"
        ),
        value_input_option: str = Field(
            default="USER_ENTERED",
            description="RAW or USER_ENTERED",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> UpdateSheetRangeResponse:
        """Overwrite a spreadsheet range with values.

        Capabilities: drive.update_sheet_range
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return UpdateSheetRangeResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            parsed = _parse_values(values)
            result = get_sheets(credentials_path, credentials_json).update_range(
                spreadsheet_id, range, parsed, value_input_option=value_input_option
            )
            return UpdateSheetRangeResponse(success=True, spreadsheet_id=spreadsheet_id, **result)
        except (DriveError, ValueError, json.JSONDecodeError) as e:
            if isinstance(e, DriveError):
                logger.error(f"update_sheet_range failed: {e.message}")
                return UpdateSheetRangeResponse(success=False, error=error_dict(e))
            return UpdateSheetRangeResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": str(e),
                    "retryable": False,
                    "original_provider_error": None,
                },
            )

    @mcp.tool()
    def append_sheet_rows(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        values: Union[List[List[Any]], str] = Field(
            ..., description="2D array of rows to append, or JSON string"
        ),
        range: str = Field(
            default="Sheet1",
            description="Sheet/table range to append into (A1 notation or sheet name)",
        ),
        value_input_option: str = Field(
            default="USER_ENTERED",
            description="RAW or USER_ENTERED",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> AppendSheetRowsResponse:
        """Append rows to a spreadsheet sheet/table.

        Capabilities: drive.append_sheet_rows
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return AppendSheetRowsResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            parsed = _parse_values(values)
            result = get_sheets(credentials_path, credentials_json).append_rows(
                spreadsheet_id, range, parsed, value_input_option=value_input_option
            )
            return AppendSheetRowsResponse(success=True, spreadsheet_id=spreadsheet_id, **result)
        except (DriveError, ValueError, json.JSONDecodeError) as e:
            if isinstance(e, DriveError):
                logger.error(f"append_sheet_rows failed: {e.message}")
                return AppendSheetRowsResponse(success=False, error=error_dict(e))
            return AppendSheetRowsResponse(
                success=False,
                error={
                    "error_code": "VALIDATION_ERROR",
                    "error_message": str(e),
                    "retryable": False,
                    "original_provider_error": None,
                },
            )

    @mcp.tool()
    def clear_sheet_range(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        range: str = Field(..., description="A1 notation range to clear"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ClearSheetRangeResponse:
        """Clear values in a spreadsheet range.

        Capabilities: drive.clear_sheet_range
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ClearSheetRangeResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            cleared = get_sheets(credentials_path, credentials_json).clear_range(
                spreadsheet_id, range
            )
            return ClearSheetRangeResponse(
                success=True, spreadsheet_id=spreadsheet_id, cleared_range=cleared
            )
        except DriveError as e:
            logger.error(f"clear_sheet_range failed: {e.message}")
            return ClearSheetRangeResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def add_sheet_tab(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        title: str = Field(..., description="New tab title"),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> AddSheetTabResponse:
        """Add a new tab to a spreadsheet.

        Capabilities: drive.add_sheet_tab
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return AddSheetTabResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            result = get_sheets(credentials_path, credentials_json).add_tab(
                spreadsheet_id, title
            )
            return AddSheetTabResponse(success=True, spreadsheet_id=spreadsheet_id, **result)
        except DriveError as e:
            logger.error(f"add_sheet_tab failed: {e.message}")
            return AddSheetTabResponse(success=False, error=error_dict(e))

    @mcp.tool()
    def export_spreadsheet(
        spreadsheet_id: str = Field(..., description="Spreadsheet ID"),
        export_format: str = Field(
            default="xlsx",
            description="Export format: csv, xlsx, or pdf",
        ),
        credentials_path: Optional[str] = Field(default=None, description="Path to OAuth token JSON"),
        credentials_json: Optional[str] = Field(default=None, description="OAuth token JSON string"),
    ) -> ExportSpreadsheetResponse:
        """Export a spreadsheet via Drive export (csv/xlsx/pdf).

        Capabilities: drive.export_spreadsheet
Outputs: success
        """
        try:
            if credentials_missing(credentials_path, credentials_json):
                return ExportSpreadsheetResponse(success=False, error=CREDENTIALS_REQUIRED_ERROR)
            content, mime = get_sheets(credentials_path, credentials_json).export_spreadsheet(
                spreadsheet_id, export_format
            )
            if mime.startswith("text/"):
                return ExportSpreadsheetResponse(
                    success=True,
                    spreadsheet_id=spreadsheet_id,
                    mime_type=mime,
                    content_text=content.decode("utf-8", errors="replace"),
                )
            return ExportSpreadsheetResponse(
                success=True,
                spreadsheet_id=spreadsheet_id,
                mime_type=mime,
                content_base64=base64.b64encode(content).decode("ascii"),
            )
        except DriveError as e:
            logger.error(f"export_spreadsheet failed: {e.message}")
            return ExportSpreadsheetResponse(success=False, error=error_dict(e))
