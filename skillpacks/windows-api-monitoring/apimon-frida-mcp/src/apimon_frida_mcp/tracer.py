from __future__ import annotations

import os
import shlex
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .decoding import enrich_event
from .definitions import DefinitionIndex
from .hooks import build_hook_specs, generate_trace_script
from .models import TraceEvent


@dataclass(slots=True)
class TraceSession:
    id: str
    pid: int
    apis: list[str]
    mode: str
    started_at: float
    status: str = "running"
    events: list[TraceEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    device: Any = None
    session: Any = None
    script: Any = None
    timer: threading.Timer | None = None
    event_limit: int = 1000


class FridaTraceManager:
    def __init__(self, index: DefinitionIndex, max_buffer_bytes: int = 256) -> None:
        self.index = index
        self.max_buffer_bytes = max_buffer_bytes
        self._sessions: dict[str, TraceSession] = {}
        self._lock = threading.RLock()

    def trace_spawn(
        self,
        command: str,
        apis: list[str],
        duration: float | None = None,
        event_limit: int = 1000,
    ) -> TraceSession:
        frida = _import_frida()
        argv = split_command(command)
        if not argv:
            raise ValueError("command must not be empty")
        device = frida.get_local_device()
        pid = device.spawn(argv)
        session = self._attach_loaded_script(device, pid, apis, "spawn", event_limit, duration)
        device.resume(pid)
        return session

    def trace_attach(
        self,
        pid: int,
        apis: list[str],
        duration: float | None = None,
        event_limit: int = 1000,
    ) -> TraceSession:
        frida = _import_frida()
        device = frida.get_local_device()
        return self._attach_loaded_script(device, pid, apis, "attach", event_limit, duration)

    def _attach_loaded_script(
        self,
        device: Any,
        pid: int,
        apis: list[str],
        mode: str,
        event_limit: int,
        duration: float | None,
    ) -> TraceSession:
        hook_specs = build_hook_specs(self.index, apis)
        source = generate_trace_script(hook_specs, max_buffer_bytes=self.max_buffer_bytes)
        frida_session = device.attach(pid)
        script = frida_session.create_script(source)
        trace_id = uuid.uuid4().hex
        trace = TraceSession(
            id=trace_id,
            pid=int(pid),
            apis=apis,
            mode=mode,
            started_at=time.time(),
            device=device,
            session=frida_session,
            script=script,
            event_limit=event_limit,
        )

        script.on("message", lambda message, data: self._on_message(trace_id, message, data))
        script.load()
        if duration is not None and duration > 0:
            timer = threading.Timer(duration, lambda: self.stop_trace(trace_id))
            timer.daemon = True
            trace.timer = timer
            timer.start()

        with self._lock:
            self._sessions[trace_id] = trace
        return trace

    def stop_trace(self, trace_id: str) -> TraceSession:
        with self._lock:
            trace = self._sessions.get(trace_id)
        if trace is None:
            raise KeyError(f"trace not found: {trace_id}")
        if trace.status != "running":
            return trace

        trace.status = "stopping"
        if trace.timer is not None:
            trace.timer.cancel()
        try:
            if trace.script is not None:
                trace.script.unload()
        except Exception as exc:  # pragma: no cover - depends on Frida runtime
            trace.errors.append(f"script unload failed: {exc}")
        try:
            if trace.session is not None:
                trace.session.detach()
        except Exception as exc:  # pragma: no cover - depends on Frida runtime
            trace.errors.append(f"session detach failed: {exc}")
        trace.status = "stopped"
        return trace

    def get_trace(self, trace_id: str) -> TraceSession:
        with self._lock:
            trace = self._sessions.get(trace_id)
        if trace is None:
            raise KeyError(f"trace not found: {trace_id}")
        return trace

    def list_events(self, trace_id: str, limit: int = 100, cursor: int = 0) -> tuple[list[TraceEvent], int | None]:
        trace = self.get_trace(trace_id)
        start = max(cursor, 0)
        end = min(start + max(limit, 0), len(trace.events))
        next_cursor = end if end < len(trace.events) else None
        return trace.events[start:end], next_cursor

    def export_trace(self, trace_id: str, format: str = "jsonl") -> str:
        import json

        trace = self.get_trace(trace_id)
        if format.lower() != "jsonl":
            raise ValueError("only jsonl export is supported in V1")
        return "\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in trace.events)

    def _on_message(self, trace_id: str, message: dict[str, Any], data: Any) -> None:
        with self._lock:
            trace = self._sessions.get(trace_id)
        if trace is None:
            return

        if message.get("type") == "send":
            payload = message.get("payload", {})
            payload_type = payload.get("type")
            if payload_type == "apimon.trace_event":
                event = enrich_event(self.index, payload.get("event", {}))
                with self._lock:
                    if len(trace.events) < trace.event_limit:
                        event["trace_id"] = trace_id
                        event["sequence"] = len(trace.events)
                        event["timestamp"] = time.time()
                        trace.events.append(event)
                    else:
                        trace.errors.append(f"event limit reached ({trace.event_limit})")
                        self.stop_trace(trace_id)
            elif payload_type == "apimon.hook_loaded":
                trace.hooks.append(f"{payload.get('api')} -> {payload.get('export_name')} @ {payload.get('address')}")
            elif payload_type == "apimon.trace_error":
                trace.errors.append(str(payload))
        elif message.get("type") == "error":
            trace.errors.append(message.get("stack") or message.get("description") or str(message))


def split_command(command: str) -> list[str]:
    return shlex.split(command, posix=(os.name != "nt"))


def _import_frida() -> Any:
    try:
        import frida
    except ModuleNotFoundError as exc:
        raise RuntimeError("Frida is not installed. Run `uv sync` on the Windows target first.") from exc
    return frida
