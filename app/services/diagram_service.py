"""
draw.io (diagrams.net) helpers via Google Drive file content.

There is no Google Draw.io API. Diagrams are Drive files with mxfile XML.
"""

import base64
from typing import List, Optional, Tuple

from app.core.exceptions import GoogleWorkspaceError
from app.schemas.drive import FileMetadata
from app.services.drive_service import DriveService

DRAWIO_MIME = "application/vnd.jgraph.mxfile"
MAX_DIAGRAM_BYTES = 5 * 1024 * 1024
# Cap XML returned to agents to reduce context flooding / injection surface
MAX_AGENT_DIAGRAM_CHARS = 200_000

EMPTY_MXFILE = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="google-drive-mcp" version="22.0.0" type="device">
  <diagram id="page-1" name="Page-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


class DiagramService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._drive = DriveService(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    def create_diagram(
        self,
        name: str = "Untitled.drawio",
        parent_folder_id: Optional[str] = None,
        content_xml: Optional[str] = None,
    ) -> dict:
        if not name.endswith(".drawio") and not name.endswith(".drawio.xml"):
            name = f"{name}.drawio"
        xml = content_xml or EMPTY_MXFILE
        content_bytes = xml.encode("utf-8")
        if len(content_bytes) > MAX_DIAGRAM_BYTES:
            raise GoogleWorkspaceError(
                f"Diagram content exceeds {MAX_DIAGRAM_BYTES} bytes",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        # Parents are set at Drive create time (single step). Success means applied.
        result = self._drive.upload_file(
            file_name=name,
            content_base64=content_b64,
            parent_folder_id=parent_folder_id,
            mime_type=DRAWIO_MIME,
        )
        parent_applied = bool(parent_folder_id)
        return {
            "file_id": result.get("id"),
            "file_name": result.get("name"),
            "web_view_link": result.get("webViewLink"),
            "parent_applied": parent_applied,
            "parent_error": None,
        }

    def list_diagrams(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> Tuple[List[FileMetadata], Optional[str]]:
        # Match common draw.io MIME types and filename extensions
        query = (
            "(mimeType='application/vnd.jgraph.mxfile' "
            "or mimeType='application/x-drawio' "
            "or name contains '.drawio')"
        )
        return self._drive.list_files(
            folder_id=folder_id,
            page_size=page_size,
            page_token=page_token,
            query=query,
            include_root_parent=folder_id is None,
        )

    def read_diagram(self, file_id: str) -> dict:
        content, mime_type, file_name = self._drive.download_file(file_id)
        if len(content) > MAX_DIAGRAM_BYTES:
            raise GoogleWorkspaceError(
                f"Diagram content exceeds {MAX_DIAGRAM_BYTES} bytes",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        try:
            content_xml = content.decode("utf-8")
            truncated = False
            if len(content_xml) > MAX_AGENT_DIAGRAM_CHARS:
                content_xml = content_xml[:MAX_AGENT_DIAGRAM_CHARS]
                truncated = True
            return {
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "content_xml": content_xml,
                "content_base64": None,
                "truncated": truncated,
            }
        except UnicodeDecodeError:
            return {
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "content_xml": None,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "truncated": False,
            }

    def update_diagram(
        self,
        file_id: str,
        content_xml: Optional[str] = None,
        content_base64: Optional[str] = None,
    ) -> dict:
        if not content_xml and not content_base64:
            raise GoogleWorkspaceError(
                "Provide content_xml or content_base64",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        if content_xml:
            content_bytes = content_xml.encode("utf-8")
        else:
            content_bytes = base64.b64decode(content_base64)
        if len(content_bytes) > MAX_DIAGRAM_BYTES:
            raise GoogleWorkspaceError(
                f"Diagram content exceeds {MAX_DIAGRAM_BYTES} bytes",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        result = self._drive.update_file_content(
            file_id=file_id,
            content_bytes=content_bytes,
            mime_type=DRAWIO_MIME,
        )
        return {
            "file_id": result.get("id", file_id),
            "file_name": result.get("name"),
            "message": "Diagram updated",
        }

    def export_diagram(self, file_id: str, export_format: str = "xml") -> dict:
        """
        Best-effort export. Server-side PNG/PDF conversion is not available
        without diagrams.net; return XML or raw stored bytes.
        """
        content, mime_type, file_name = self._drive.download_file(file_id)
        if len(content) > MAX_DIAGRAM_BYTES:
            raise GoogleWorkspaceError(
                f"Diagram content exceeds {MAX_DIAGRAM_BYTES} bytes",
                error_code="PAYLOAD_TOO_LARGE",
                retryable=False,
            )
        export_format = (export_format or "xml").lower()
        if export_format in ("xml", "drawio", "mxfile"):
            xml = content.decode("utf-8", errors="replace")
            truncated = False
            if len(xml) > MAX_AGENT_DIAGRAM_CHARS:
                xml = xml[:MAX_AGENT_DIAGRAM_CHARS]
                truncated = True
            note = "Returned draw.io mxfile XML. PNG/PDF conversion requires diagrams.net client."
            if truncated:
                note += f" Truncated to {MAX_AGENT_DIAGRAM_CHARS} chars for agent context safety."
            return {
                "file_id": file_id,
                "mime_type": mime_type or DRAWIO_MIME,
                "content_xml": xml,
                "content_base64": None,
                "note": note,
            }
        if export_format in ("svg", "png") and (
            "svg" in (mime_type or "") or "png" in (mime_type or "")
        ):
            return {
                "file_id": file_id,
                "mime_type": mime_type,
                "content_xml": None,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "note": f"Returned stored {mime_type} bytes (file already in that format).",
            }
        raise GoogleWorkspaceError(
            "Server-side PNG/PDF export is not supported. "
            "Use export_format='xml' or open the file in diagrams.net.",
            error_code="UNSUPPORTED_EXPORT",
            retryable=False,
        )
