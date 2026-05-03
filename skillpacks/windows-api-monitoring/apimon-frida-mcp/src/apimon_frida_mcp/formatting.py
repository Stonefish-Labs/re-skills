from __future__ import annotations

from .decoding import describe_value_decoder
from .definitions import DefinitionIndex
from .models import ApiDef, SearchResult
from .tracer import TraceSession


def format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "No matching definitions found."
    lines = ["# Definition Search", "", "| Kind | Name | Detail |", "|---|---|---|"]
    for item in results:
        detail = item.detail.replace("|", "\\|")
        lines.append(f"| {item.kind} | `{item.name}` | {detail} |")
    return "\n".join(lines)


def format_api_description(index: DefinitionIndex, api: ApiDef) -> str:
    lines = [
        f"# {api.display_name}",
        "",
        f"```c\n{api.signature()}\n```",
        "",
        f"**Category:** {api.category or 'uncategorized'}",
        f"**Calling convention:** {api.calling_convention or 'unknown'}",
        f"**Error function:** {api.error_func or 'none'}",
        f"**Source:** {api.source or 'unknown'}",
        "",
        "## Parameters",
        "",
        "| Name | Type | Hints | Decoder |",
        "|---|---|---|---|",
    ]
    for param in api.params:
        hints = []
        for key in ["Length", "PostLength", "Count", "DerefPostCount", "OutputOnly"]:
            if key in param.attrs:
                hints.append(f"{key}={param.attrs[key]}")
        decoder = describe_value_decoder(index, param.type) or ""
        lines.append(f"| `{param.name}` | `{param.type}` | {'; '.join(hints)} | {decoder} |")
    lines.extend(
        [
            "",
            "## Return",
            "",
            f"`{api.return_def.type}`",
        ]
    )
    if api.success:
        lines.append(f"Success rule: `{api.success.relation or 'default'} {api.success.value or ''}`")
    return_decoder = describe_value_decoder(index, api.return_def.type)
    if return_decoder:
        lines.append(return_decoder)
    return "\n".join(lines)


def format_trace_started(trace: TraceSession) -> str:
    return (
        f"# Trace Started\n\n"
        f"**Trace ID:** `{trace.id}`\n"
        f"**PID:** `{trace.pid}`\n"
        f"**Mode:** {trace.mode}\n"
        f"**APIs:** {', '.join(f'`{api}`' for api in trace.apis)}\n"
        f"**Status:** {trace.status}\n"
    )


def format_trace_stopped(trace: TraceSession) -> str:
    return (
        f"# Trace Stopped\n\n"
        f"**Trace ID:** `{trace.id}`\n"
        f"**Events:** {len(trace.events)}\n"
        f"**Hooks:** {len(trace.hooks)}\n"
        f"**Errors:** {len(trace.errors)}\n"
    )


def format_events_summary(trace_id: str, events: list[dict], next_cursor: int | None) -> str:
    lines = [f"# Trace Events `{trace_id}`", "", f"Returned {len(events)} event(s)."]
    if next_cursor is not None:
        lines.append(f"Next cursor: `{next_cursor}`")
    if events:
        lines.extend(["", "| Seq | API | Return | Success |", "|---:|---|---|---|"])
        for event in events[:20]:
            lines.append(
                f"| {event.get('sequence')} | `{event.get('api')}` | `{event.get('return_value')}` | {event.get('success')} |"
            )
    return "\n".join(lines)
