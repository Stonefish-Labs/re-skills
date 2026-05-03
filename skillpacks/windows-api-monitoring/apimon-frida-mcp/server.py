from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from apimon_frida_mcp.config import discover_xml_root
from apimon_frida_mcp.definitions import ApiMonitorDefinitions, DefinitionIndex
from apimon_frida_mcp.formatting import (
    format_api_description,
    format_events_summary,
    format_search_results,
    format_trace_started,
    format_trace_stopped,
)
from apimon_frida_mcp.mcp_utils import structured_response, text_response
from apimon_frida_mcp.tracer import FridaTraceManager


mcp = FastMCP(
    "API Monitor Frida MCP",
    instructions=(
        "Trace Windows API calls with Frida and decode older Win32 calls using API Monitor XML. "
        "Use read-only tracing tools for spawn/attach sessions; V1 does not mutate calls."
    ),
    on_duplicate="error",
)

_state_lock = threading.RLock()
_definitions: ApiMonitorDefinitions | None = None
_manager: FridaTraceManager | None = None


def _xml_root() -> Path:
    return discover_xml_root(PROJECT_ROOT, env=os.environ)


def _index() -> DefinitionIndex:
    global _definitions
    with _state_lock:
        if _definitions is None:
            _definitions = ApiMonitorDefinitions(_xml_root())
        return _definitions.load_all()


def _trace_manager() -> FridaTraceManager:
    global _manager
    index = _index()
    with _state_lock:
        if _manager is None:
            _manager = FridaTraceManager(index)
        return _manager


@mcp.tool(annotations={"readOnlyHint": True})
def search_definitions(
    query: str,
    kind: Literal["api", "type", "enum", "flag", "interface"] | None = None,
    module: str | None = None,
    limit: Annotated[int, Field(ge=1, le=200)] = 50,
) -> ToolResult:
    """Search API Monitor XML definitions by API, type, enum, flag, or interface name."""
    try:
        results = _index().search(query=query, kind=kind, module=module, limit=limit)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return text_response(format_search_results(results))


@mcp.tool(annotations={"readOnlyHint": True})
def describe_api(module: str, function: str) -> ToolResult:
    """Describe a decoded API signature and its known parameter/return metadata."""
    index = _index()
    api = index.find_api(function, module=module)
    if api is None:
        raise ToolError(f"API definition not found: {module}!{function}")
    return text_response(format_api_description(index, api))


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def trace_spawn(
    command: str,
    apis: list[str],
    duration: Annotated[float | None, Field(gt=0)] = None,
    event_limit: Annotated[int, Field(ge=1, le=100000)] = 1000,
) -> ToolResult:
    """Launch a process under Frida and trace selected API definitions."""
    if not apis:
        raise ToolError("At least one API must be provided, e.g. ['Kernel32!ReadFile'].")
    try:
        trace = _trace_manager().trace_spawn(command, apis, duration=duration, event_limit=event_limit)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return structured_response(format_trace_started(trace), {"trace_id": trace.id, "pid": trace.pid, "status": trace.status})


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def trace_attach(
    pid: Annotated[int, Field(ge=1)],
    apis: list[str],
    duration: Annotated[float | None, Field(gt=0)] = None,
    event_limit: Annotated[int, Field(ge=1, le=100000)] = 1000,
) -> ToolResult:
    """Attach to an existing process with Frida and trace selected API definitions."""
    if not apis:
        raise ToolError("At least one API must be provided, e.g. ['Kernel32!ReadFile'].")
    try:
        trace = _trace_manager().trace_attach(pid, apis, duration=duration, event_limit=event_limit)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return structured_response(format_trace_started(trace), {"trace_id": trace.id, "pid": trace.pid, "status": trace.status})


@mcp.tool(annotations={"readOnlyHint": False})
def stop_trace(trace_id: str) -> ToolResult:
    """Stop a running trace and detach Frida from the target process."""
    try:
        trace = _trace_manager().stop_trace(trace_id)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return structured_response(
        format_trace_stopped(trace),
        {"trace_id": trace.id, "status": trace.status, "events": len(trace.events), "errors": trace.errors},
    )


@mcp.tool(annotations={"readOnlyHint": True})
def get_trace_events(
    trace_id: str,
    limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    cursor: Annotated[int, Field(ge=0)] = 0,
) -> ToolResult:
    """Retrieve decoded trace events from an in-memory trace session."""
    try:
        manager = _trace_manager()
        events, next_cursor = manager.list_events(trace_id, limit=limit, cursor=cursor)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return structured_response(
        format_events_summary(trace_id, events, next_cursor),
        {"trace_id": trace_id, "events": events, "next_cursor": next_cursor},
    )


@mcp.tool(annotations={"readOnlyHint": True})
def export_trace(trace_id: str, format: Literal["jsonl"] = "jsonl") -> ToolResult:
    """Export captured trace events as JSONL text."""
    try:
        exported = _trace_manager().export_trace(trace_id, format=format)
    except Exception as exc:
        raise ToolError(str(exc)) from exc
    return structured_response(
        exported or "",
        {"trace_id": trace_id, "format": format, "bytes": len(exported.encode("utf-8"))},
    )


if __name__ == "__main__":
    mcp.run()
