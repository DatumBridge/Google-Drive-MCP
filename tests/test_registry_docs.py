"""Tests for registry_docs contract compliance according to ADR-0132 and mcp-tool-contract.md."""

import json
import os
import re
from pathlib import Path
import pytest

from app.mcp_server import mcp

REGISTRY_DOCS_DIR = Path(__file__).resolve().parent.parent / "registry_docs"


def get_all_tool_names():
    # FastMCP stores tools in mcp._tool_manager or inspectable via list_tools or mcp._tool_manager._tools
    # In FastMCP:
    try:
        tools = list(mcp._tool_manager._tools.keys())
    except Exception:
        # Fallback to test_mcp_tools expected tools
        from scripts.test_mcp_tools import EXPECTED_TOOLS
        tools = EXPECTED_TOOLS
    return sorted(tools)


def get_all_registry_doc_files():
    return sorted([f for f in REGISTRY_DOCS_DIR.glob("*.md")])


class TestRegistryDocsContract:
    @pytest.fixture(scope="class")
    def tool_names(self):
        return get_all_tool_names()

    @pytest.fixture(scope="class")
    def doc_files(self):
        return get_all_registry_doc_files()

    def test_doc_count_and_tool_parity(self, tool_names, doc_files):
        """Every @mcp.tool has a corresponding registry_docs/<name>.md and vice versa."""
        doc_names = [f.stem for f in doc_files]
        assert len(doc_files) == 40, f"Expected 40 doc files, found {len(doc_files)}"
        assert len(tool_names) == 40, f"Expected 40 tools, found {len(tool_names)}"
        assert set(tool_names) == set(doc_names), f"Mismatch between tools and docs: {set(tool_names) ^ set(doc_names)}"

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_file_size_limit(self, doc_path):
        """Doc size must be <= 24,000 characters."""
        content = doc_path.read_text(encoding="utf-8")
        assert len(content) <= 24000, f"{doc_path.name} exceeds 24,000 chars: {len(content)}"

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_required_sections_and_phrases(self, doc_path):
        """Doc must contain required headers and key agent safety phrases."""
        content = doc_path.read_text(encoding="utf-8")

        assert "## Agent rules" in content, f"{doc_path.name} missing '## Agent rules'"
        assert "## When to call" in content, f"{doc_path.name} missing '## When to call'"
        assert "## Parameters" in content, f"{doc_path.name} missing '## Parameters'"
        assert "## Success fields" in content, f"{doc_path.name} missing '## Success fields'"
        assert "## Error codes" in content, f"{doc_path.name} missing '## Error codes'"
        assert "## Cases" in content, f"{doc_path.name} missing '## Cases'"

        # ADR-0132 Required phrases
        assert "untrusted" in content, f"{doc_path.name} missing 'untrusted' in rules"
        assert "Do not invent a token" in content, f"{doc_path.name} missing 'Do not invent a token'"

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_parameter_table_format(self, doc_path):
        """Parameters table must have 6 columns matching Name, Required, Type, Sample, Related tool, Meaning."""
        content = doc_path.read_text(encoding="utf-8")
        
        # Look for table header under ## Parameters
        param_section = content.split("## Parameters")[1].split("## Success fields")[0]
        lines = [line.strip() for line in param_section.splitlines() if line.strip().startswith("|")]
        
        assert len(lines) >= 2, f"{doc_path.name} has no parameter table"
        header = [col.strip() for col in lines[0].split("|")[1:-1]]
        assert header == ["Name", "Required", "Type", "Sample", "Related tool", "Meaning"], (
            f"{doc_path.name} parameter table header mismatch: {header}"
        )

        # Check each parameter row has 6 columns and a sample
        for row in lines[2:]:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            assert len(cols) == 6, f"{doc_path.name} row does not have 6 columns: {row}"
            name, req, typ, sample, related, meaning = cols
            if typ.lower() not in ("none", "void"):
                assert sample != "", f"{doc_path.name} param {name} has empty Sample"

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_error_codes_rules(self, doc_path):
        """Error codes section must not use invalid_argument (which is a JSON-RPC code)."""
        content = doc_path.read_text(encoding="utf-8")
        error_section = content.split("## Error codes")[1].split("## Cases")[0]
        assert "invalid_argument" not in error_section.lower(), (
            f"{doc_path.name} contains invalid_argument in Error codes"
        )
        assert "CREDENTIALS_REQUIRED" in error_section
        assert "AUTH_ERROR" in error_section

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_cases_structure(self, doc_path):
        """Cases must contain Typical call, Missing required field (or note), and Provider not found."""
        content = doc_path.read_text(encoding="utf-8")
        cases_section = content.split("## Cases")[1]

        assert "### Typical call" in cases_section, f"{doc_path.name} missing '### Typical call'"
        assert "### Missing required field" in cases_section, f"{doc_path.name} missing '### Missing required field'"
        assert "### Provider not found" in cases_section, f"{doc_path.name} missing '### Provider not found'"

        # Verify JSON-RPC -32602 documented in missing required field
        missing_section = cases_section.split("### Missing required field")[1].split("### Provider not found")[0]
        assert "-32602" in missing_section, f"{doc_path.name} missing -32602 in Missing required field case"

    @pytest.mark.parametrize("doc_path", get_all_registry_doc_files(), ids=lambda p: p.name)
    def test_typical_call_no_credentials(self, doc_path):
        """Typical call input JSON must never contain credentials_json, credentials_path, or access_token."""
        content = doc_path.read_text(encoding="utf-8")
        typical_section = content.split("### Typical call")[1].split("### Missing required field")[0]

        # Extract input json block
        input_match = re.search(r"Input:\s*```json\s*(\{.*?\})\s*```", typical_section, re.DOTALL)
        assert input_match, f"{doc_path.name} could not parse Typical call input JSON"
        input_json_str = input_match.group(1)
        input_data = json.loads(input_json_str)

        assert "credentials_json" not in input_data, f"{doc_path.name} input has credentials_json"
        assert "credentials_path" not in input_data, f"{doc_path.name} input has credentials_path"
        assert "access_token" not in input_data, f"{doc_path.name} input has access_token"
