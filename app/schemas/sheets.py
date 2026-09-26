"""Pydantic models for Google Sheets MCP tools."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ErrorResponse


class SheetTabInfo(BaseModel):
    sheet_id: int
    title: str
    index: int = 0


class CreateSpreadsheetResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    title: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    parent_applied: Optional[bool] = None
    parent_error: Optional[ErrorResponse] = None
    error: Optional[ErrorResponse] = None


class ListSheetTabsResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    tabs: List[SheetTabInfo] = Field(default_factory=list)
    error: Optional[dict] = None


class ReadSheetRangeResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    range: Optional[str] = None
    resolved_range: Optional[str] = None
    values: List[List[Any]] = Field(default_factory=list)
    error: Optional[dict] = None


class UpdateSheetRangeResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    updated_range: Optional[str] = None
    updated_rows: Optional[int] = None
    updated_columns: Optional[int] = None
    updated_cells: Optional[int] = None
    error: Optional[dict] = None


class AppendSheetRowsResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    updated_range: Optional[str] = None
    updated_rows: Optional[int] = None
    error: Optional[dict] = None


class ClearSheetRangeResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    cleared_range: Optional[str] = None
    error: Optional[dict] = None


class AddSheetTabResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    sheet_id: Optional[int] = None
    title: Optional[str] = None
    error: Optional[dict] = None


class ExportSpreadsheetResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    mime_type: Optional[str] = None
    content_base64: Optional[str] = None
    content_text: Optional[str] = None
    error: Optional[dict] = None
