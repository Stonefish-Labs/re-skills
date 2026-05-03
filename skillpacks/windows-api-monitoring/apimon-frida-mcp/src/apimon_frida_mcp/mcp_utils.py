from __future__ import annotations

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent


def text_response(text: str) -> ToolResult:
    """Return raw text without JSON wrapping overhead."""
    return ToolResult(content=[TextContent(type="text", text=text)], structured_content=None)


def structured_response(text: str, data: dict, meta: dict | None = None) -> ToolResult:
    """Return text for agents and structured content for automation."""
    return ToolResult(content=[TextContent(type="text", text=text)], structured_content=data, meta=meta)
