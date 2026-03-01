#!/usr/bin/env python3
"""
Test script for Google Drive MCP Server tools.

Tests all 7 MCP tools: upload_file, download_file, list_files, create_folder,
move_file, delete_file, get_file_metadata.

Usage:
    # Test without credentials (validates tool structure, expects CREDENTIALS_REQUIRED):
    python scripts/test_mcp_tools.py

    # Test with OAuth token (full integration):
    python scripts/test_mcp_tools.py --credentials-path token.json

    # Or with JSON string:
    python scripts/test_mcp_tools.py --credentials-json "$(cat token.json)"

    # Custom server URL:
    python scripts/test_mcp_tools.py --url http://localhost:8000/mcp
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Try FastMCP Client first, fall back to raw HTTP
USE_FASTMCP = False
try:
    from fastmcp import Client
    USE_FASTMCP = True
except ImportError:
    try:
        import httpx
    except ImportError:
        print("Error: Install dependencies: pip install fastmcp (or pip install httpx for raw HTTP)")
        sys.exit(1)


# Default MCP server URL (trailing slash required by FastMCP)
DEFAULT_URL = "http://localhost:8000/mcp/"

# Test parameters
TEST_FOLDER_NAME = "mcp-test-folder"
TEST_FILE_NAME = "mcp-test-file.txt"
TEST_FILE_CONTENT = "Hello from MCP test script!"


def get_credentials_args(credentials_path: Optional[str], credentials_json: Optional[str]) -> dict:
    """Build credentials dict for tool calls."""
    if credentials_path and Path(credentials_path).exists():
        return {"credentials_path": credentials_path}
    if credentials_json:
        return {"credentials_json": credentials_json}
    return {}


def _tool_result(result: Any) -> Tuple[bool, dict]:
    """Extract success and data from tool result (dict or Pydantic model)."""
    if isinstance(result, dict):
        return result.get("success", False), result
    # Pydantic model (has model_dump) or object
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    else:
        data = vars(result) if hasattr(result, "__dict__") else {}
    return data.get("success", False), data


# ============== Raw HTTP/JSON-RPC client (fallback) ==============

def _mcp_request(url: str, method: str, params: Optional[dict] = None, request_id: int = 1) -> dict:
    """Send JSON-RPC request to MCP server."""
    import httpx
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data.get("result", data)


def _call_tool_http(url: str, name: str, arguments: dict) -> Any:
    """Call MCP tool via raw HTTP."""
    result = _mcp_request(url, "tools/call", {"name": name, "arguments": arguments}, request_id=100)
    # Result may have content array with text
    content = result.get("content", [])
    if content and isinstance(content[0], dict):
        text = content[0].get("text", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    return result


def _list_tools_http(url: str) -> list:
    """List tools via raw HTTP."""
    result = _mcp_request(url, "tools/list", request_id=99)
    tools = result.get("tools", [])
    return [t.get("name", "") for t in tools]


# ============== Test runner (sync, works with both clients) ==============

def run_tests_http(
    url: str,
    credentials_path: Optional[str],
    credentials_json: Optional[str],
) -> tuple:
    """Run tests using raw HTTP client."""
    import httpx
    creds = get_credentials_args(credentials_path, credentials_json)
    has_creds = bool(creds)
    passed = 0
    failed = 0

    # 1. List tools (FastMCP may handle init automatically via session)
    try:
        tool_names = _list_tools_http(url)
        expected = {
            "upload_file", "download_file", "list_files", "create_folder",
            "move_file", "delete_file", "get_file_metadata",
        }
        missing = expected - set(tool_names)
        if missing:
            print(f"FAIL: Missing tools: {missing}")
            failed += 1
        else:
            print(f"PASS: All 7 tools registered: {sorted(tool_names)}")
            passed += 1
    except Exception as e:
        print(f"FAIL: list_tools: {e}")
        failed += 1
        return passed, failed

    # 2. list_files
    print("\n--- Test: list_files (root) ---")
    try:
        data = _call_tool_http(url, "list_files", {**creds})
        success = data.get("success", False)
        error = data.get("error", {})
        if not has_creds:
            if not success and error.get("error_code") == "CREDENTIALS_REQUIRED":
                print("PASS: list_files correctly requires credentials")
                passed += 1
            else:
                print(f"FAIL: Expected CREDENTIALS_REQUIRED, got: {data}")
                failed += 1
        else:
            if success:
                count = data.get("total_count", 0)
                print(f"PASS: list_files returned {count} items")
                passed += 1
            else:
                print(f"FAIL: list_files: {error}")
                failed += 1
    except Exception as e:
        print(f"FAIL: list_files: {e}")
        failed += 1

    if not has_creds:
        print("\n(Provide --credentials-path or --credentials-json for full integration tests)")
        return passed, failed

    # 3-8. Full integration tests
    folder_id = None
    file_id = None
    dest_folder_id = None

    try:
        # create_folder
        print("\n--- Test: create_folder ---")
        data = _call_tool_http(url, "create_folder", {"folder_name": TEST_FOLDER_NAME, **creds})
        if data.get("success"):
            folder_id = data.get("folder_id")
            print(f"PASS: create_folder -> folder_id={folder_id}")
            passed += 1
        else:
            print(f"FAIL: create_folder: {data}")
            failed += 1
            return passed, failed

        # upload_file
        print("\n--- Test: upload_file ---")
        content_b64 = base64.b64encode(TEST_FILE_CONTENT.encode()).decode()
        data = _call_tool_http(url, "upload_file", {
            "file_name": TEST_FILE_NAME,
            "content_base64": content_b64,
            "parent_folder_id": folder_id,
            **creds,
        })
        if data.get("success"):
            file_id = data.get("file_id")
            print(f"PASS: upload_file -> file_id={file_id}")
            passed += 1
        else:
            print(f"FAIL: upload_file: {data}")
            failed += 1
            return passed, failed

        # get_file_metadata
        print("\n--- Test: get_file_metadata ---")
        data = _call_tool_http(url, "get_file_metadata", {"file_id": file_id, **creds})
        if data.get("success"):
            meta = data.get("metadata", {})
            print(f"PASS: get_file_metadata -> name={meta.get('name')}")
            passed += 1
        else:
            print(f"FAIL: get_file_metadata: {data}")
            failed += 1

        # download_file
        print("\n--- Test: download_file ---")
        data = _call_tool_http(url, "download_file", {"file_id": file_id, "as_text": True, **creds})
        if data.get("success"):
            content = data.get("content_text", "")
            if content == TEST_FILE_CONTENT:
                print("PASS: download_file content matches")
                passed += 1
            else:
                print(f"FAIL: download_file content mismatch")
                failed += 1
        else:
            print(f"FAIL: download_file: {data}")
            failed += 1

        # move_file
        print("\n--- Test: move_file ---")
        data = _call_tool_http(url, "create_folder", {"folder_name": "mcp-test-dest", **creds})
        dest_folder_id = data.get("folder_id") if data.get("success") else None
        if dest_folder_id:
            data = _call_tool_http(url, "move_file", {
                "file_id": file_id,
                "new_parent_folder_id": dest_folder_id,
                **creds,
            })
            if data.get("success"):
                print("PASS: move_file")
                passed += 1
            else:
                print(f"FAIL: move_file: {data}")
                failed += 1
        else:
            print("FAIL: Could not create dest folder for move_file")
            failed += 1

        # delete_file
        print("\n--- Test: delete_file ---")
        data = _call_tool_http(url, "delete_file", {"file_id": file_id, **creds})
        if data.get("success"):
            print("PASS: delete_file")
            passed += 1
        else:
            print(f"FAIL: delete_file: {data}")
            failed += 1

        # Cleanup folders
        for fid in [folder_id, dest_folder_id]:
            if fid:
                _call_tool_http(url, "delete_file", {"file_id": fid, **creds})

    except Exception as e:
        print(f"FAIL: {e}")
        failed += 1

    return passed, failed


async def run_tests_fastmcp(
    url: str,
    credentials_path: Optional[str],
    credentials_json: Optional[str],
) -> tuple:
    """Run tests using FastMCP Client."""
    creds = get_credentials_args(credentials_path, credentials_json)
    has_creds = bool(creds)
    passed = 0
    failed = 0

    async with Client(url) as client:
        # 1. List tools
        try:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            expected = {
                "upload_file", "download_file", "list_files", "create_folder",
                "move_file", "delete_file", "get_file_metadata",
            }
            missing = expected - set(tool_names)
            if missing:
                print(f"FAIL: Missing tools: {missing}")
                failed += 1
            else:
                print(f"PASS: All 7 tools registered: {sorted(tool_names)}")
                passed += 1
        except Exception as e:
            print(f"FAIL: list_tools: {e}")
            failed += 1
            return passed, failed

        # 2. list_files
        print("\n--- Test: list_files (root) ---")
        try:
            result = await client.call_tool("list_files", {**creds}, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            error = data_dict.get("error") or {}
            if isinstance(error, dict):
                error_code = error.get("error_code", "")
            else:
                error_code = getattr(error, "error_code", "") if error else ""
            if not has_creds:
                if not success and error_code == "CREDENTIALS_REQUIRED":
                    print("PASS: list_files correctly requires credentials")
                    passed += 1
                else:
                    print(f"FAIL: Expected CREDENTIALS_REQUIRED, got: {data_dict}")
                    failed += 1
            else:
                if success:
                    print(f"PASS: list_files returned {data_dict.get('total_count', 0)} items")
                    passed += 1
                else:
                    print(f"FAIL: list_files: {error}")
                    failed += 1
        except Exception as e:
            print(f"FAIL: list_files: {e}")
            failed += 1

        if not has_creds:
            print("\n(Provide --credentials-path or --credentials-json for full integration tests)")
            return passed, failed

        # 3-8. Full integration
        folder_id = file_id = dest_folder_id = None
        try:
            result = await client.call_tool("create_folder", {"folder_name": TEST_FOLDER_NAME, **creds}, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            error = data_dict.get("error") or {}
            error_code = (error.get("error_code") if isinstance(error, dict) else getattr(error, "error_code", "")) if error else ""
            if success:
                folder_id = data_dict.get("folder_id")
                print(f"\n--- Test: create_folder ---\nPASS: folder_id={folder_id}")
                passed += 1
            elif error_code == "CREDENTIALS_REQUIRED":
                print("\n--- Test: create_folder ---")
                print("FAIL: Server cannot access credentials. When using Docker, mount the credentials")
                print("      into the MCP server container: docker run -v /path/to/creds.json:/creds.json:ro ...")
                failed += 1
                return passed, failed
            else:
                print(f"\n--- Test: create_folder ---\nFAIL: {data_dict}")
                failed += 1
                return passed, failed

            content_b64 = base64.b64encode(TEST_FILE_CONTENT.encode()).decode()
            result = await client.call_tool("upload_file", {
                "file_name": TEST_FILE_NAME, "content_base64": content_b64,
                "parent_folder_id": folder_id, **creds,
            }, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            if success:
                file_id = data_dict.get("file_id")
                print(f"\n--- Test: upload_file ---\nPASS: file_id={file_id}")
                passed += 1
            else:
                print(f"\n--- Test: upload_file ---\nFAIL: {data_dict}")
                failed += 1
                return passed, failed

            result = await client.call_tool("get_file_metadata", {"file_id": file_id, **creds}, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            if success:
                meta = data_dict.get("metadata") or {}
                name = meta.get("name") if isinstance(meta, dict) else getattr(meta, "name", "")
                print(f"\n--- Test: get_file_metadata ---\nPASS: name={name}")
                passed += 1
            else:
                print(f"\n--- Test: get_file_metadata ---\nFAIL: {data_dict}")
                failed += 1

            result = await client.call_tool("download_file", {"file_id": file_id, "as_text": True, **creds}, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            content_text = data_dict.get("content_text", "")
            if success and content_text == TEST_FILE_CONTENT:
                print("\n--- Test: download_file ---\nPASS: content matches")
                passed += 1
            else:
                print(f"\n--- Test: download_file ---\nFAIL: {data_dict}")
                failed += 1

            result = await client.call_tool("create_folder", {"folder_name": "mcp-test-dest", **creds}, raise_on_error=False)
            dest_data = result.data if hasattr(result, "data") else result
            _, dest_dict = _tool_result(dest_data)
            dest_folder_id = dest_dict.get("folder_id")
            if dest_folder_id:
                result = await client.call_tool("move_file", {
                    "file_id": file_id, "new_parent_folder_id": dest_folder_id, **creds,
                }, raise_on_error=False)
                data = result.data if hasattr(result, "data") else result
                success, data_dict = _tool_result(data)
                if success:
                    print("\n--- Test: move_file ---\nPASS")
                    passed += 1
                else:
                    print(f"\n--- Test: move_file ---\nFAIL: {data_dict}")
                    failed += 1
            else:
                print("\n--- Test: move_file ---\nFAIL: Could not create dest folder")
                failed += 1

            result = await client.call_tool("delete_file", {"file_id": file_id, **creds}, raise_on_error=False)
            data = result.data if hasattr(result, "data") else result
            success, data_dict = _tool_result(data)
            if success:
                print("\n--- Test: delete_file ---\nPASS")
                passed += 1
            else:
                print(f"\n--- Test: delete_file ---\nFAIL: {data_dict}")
                failed += 1

            for fid in [folder_id, dest_folder_id]:
                if fid:
                    await client.call_tool("delete_file", {"file_id": fid, **creds}, raise_on_error=False)
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1

    return passed, failed


def main():
    parser = argparse.ArgumentParser(
        description="Test Google Drive MCP Server tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("MCP_SERVER_URL", DEFAULT_URL),
        help="MCP server URL (default: %(default)s)",
    )
    parser.add_argument(
        "--credentials-path",
        default=os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH"),
        help="Path to OAuth token JSON file (e.g. token.json)",
    )
    parser.add_argument(
        "--credentials-json",
        default=os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON"),
        help="OAuth token JSON string",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use raw HTTP client instead of FastMCP (requires httpx)",
    )
    args = parser.parse_args()

    print(f"Testing Google Drive MCP Server at {args.url}")
    if args.credentials_path or args.credentials_json:
        print("Credentials: provided (full integration tests)")
    else:
        print("Credentials: not provided (structure validation only)")

    if args.http or not USE_FASTMCP:
        if not USE_FASTMCP and not args.http:
            print("(Using httpx - install fastmcp for native client)")
        passed, failed = run_tests_http(
            url=args.url,
            credentials_path=args.credentials_path,
            credentials_json=args.credentials_json,
        )
    else:
        import asyncio
        passed, failed = asyncio.run(run_tests_fastmcp(
            url=args.url,
            credentials_path=args.credentials_path,
            credentials_json=args.credentials_json,
        ))

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
