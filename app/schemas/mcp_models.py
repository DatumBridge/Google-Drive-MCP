"""
Pydantic models for Google Drive / Workspace MCP Server tools.

Re-exports domain schemas for backward compatibility with DatumBridge ADK Test UI.
"""

from app.schemas.common import ErrorResponse
from app.schemas.drive import (
    FileMetadata,
    FileListResponse,
    UploadResponse,
    DownloadResponse,
    CreateFolderResponse,
    MoveResponse,
    DeleteResponse,
    GetMetadataResponse,
)
from app.schemas.docs import (
    CreateDocumentResponse,
    ReadDocumentResponse,
    AppendDocumentTextResponse,
    ReplaceDocumentTextResponse,
    InsertDocumentTextResponse,
    ExportDocumentResponse,
)
from app.schemas.sheets import (
    SheetTabInfo,
    CreateSpreadsheetResponse,
    ListSheetTabsResponse,
    ReadSheetRangeResponse,
    UpdateSheetRangeResponse,
    AppendSheetRowsResponse,
    ClearSheetRangeResponse,
    AddSheetTabResponse,
    ExportSpreadsheetResponse,
)
from app.schemas.slides import (
    SlideInfo,
    SlideTextContent,
    CreatePresentationResponse,
    ListSlidesResponse,
    ReadPresentationResponse,
    AddSlideResponse,
    InsertSlideTextResponse,
    ReplacePresentationTextResponse,
    ExportPresentationResponse,
)
from app.schemas.forms import (
    FormQuestionSummary,
    FormResponseSummary,
    CreateFormResponse,
    GetFormResponseModel,
    UpdateFormInfoResponse,
    AddFormQuestionResponse,
    ListFormResponsesResponse,
    GetFormResponseDetailResponse,
)
from app.schemas.diagrams import (
    CreateDiagramResponse,
    ListDiagramsResponse,
    ReadDiagramResponse,
    UpdateDiagramResponse,
    ExportDiagramResponse,
)

__all__ = [
    "ErrorResponse",
    "FileMetadata",
    "FileListResponse",
    "UploadResponse",
    "DownloadResponse",
    "CreateFolderResponse",
    "MoveResponse",
    "DeleteResponse",
    "GetMetadataResponse",
    "CreateDocumentResponse",
    "ReadDocumentResponse",
    "AppendDocumentTextResponse",
    "ReplaceDocumentTextResponse",
    "InsertDocumentTextResponse",
    "ExportDocumentResponse",
    "SheetTabInfo",
    "CreateSpreadsheetResponse",
    "ListSheetTabsResponse",
    "ReadSheetRangeResponse",
    "UpdateSheetRangeResponse",
    "AppendSheetRowsResponse",
    "ClearSheetRangeResponse",
    "AddSheetTabResponse",
    "ExportSpreadsheetResponse",
    "SlideInfo",
    "SlideTextContent",
    "CreatePresentationResponse",
    "ListSlidesResponse",
    "ReadPresentationResponse",
    "AddSlideResponse",
    "InsertSlideTextResponse",
    "ReplacePresentationTextResponse",
    "ExportPresentationResponse",
    "FormQuestionSummary",
    "FormResponseSummary",
    "CreateFormResponse",
    "GetFormResponseModel",
    "UpdateFormInfoResponse",
    "AddFormQuestionResponse",
    "ListFormResponsesResponse",
    "GetFormResponseDetailResponse",
    "CreateDiagramResponse",
    "ListDiagramsResponse",
    "ReadDiagramResponse",
    "UpdateDiagramResponse",
    "ExportDiagramResponse",
]
