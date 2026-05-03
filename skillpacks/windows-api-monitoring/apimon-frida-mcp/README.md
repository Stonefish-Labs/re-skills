# API Monitor Frida MCP

FastMCP 3.x server for tracing Windows API calls with Frida while decoding calls
with the XML definitions from API Monitor.

This is designed for a Windows reverse-engineering host or VM. Codex or another
MCP client can connect over stdio locally, or through whatever remote MCP bridge
you use for Windows tooling.

## What It Provides

- `search_definitions(query, kind?, module?)`
- `describe_api(module, function)`
- `trace_spawn(command, apis, duration?, event_limit?)`
- `trace_attach(pid, apis, duration?, event_limit?)`
- `stop_trace(trace_id)`
- `get_trace_events(trace_id, limit?, cursor?)`
- `export_trace(trace_id, format="jsonl")`

V1 is read-only trace/decode. It does not mutate calls, patch arguments, or
implement breakpoint-style call editing.

## Layout

```text
apimon-frida-mcp/
  api-monitor-xml/
    Headers/
    Windows/
    Interfaces/
    ...
  src/apimon_frida_mcp/
  tests/
  server.py
  pyproject.toml
```

The `api-monitor-xml` directory is vendored from
`https://github.com/jozefizso/apimonitor` commit
`9012ca84b477e35cac1a5df5b403c193de83cb7d` (`API Monitor v2 Alpha-r13`).
See [`api-monitor-xml/SOURCE.md`](api-monitor-xml/SOURCE.md) and
[`api-monitor-xml/API_MONITOR_LICENSE.txt`](api-monitor-xml/API_MONITOR_LICENSE.txt).

## Install

```powershell
cd path\to\re-skills\skillpacks\windows-api-monitoring\apimon-frida-mcp
uv sync
```

`frida-tools` is intentionally not installed into the MCP environment because
current `frida-tools>=14` releases pin `websockets<14`, while FastMCP 3.x
requires `websockets>=15`. The server uses the `frida` Python bindings directly.
If you need standalone commands like `frida-trace`, install
[`requirements-frida-tools.txt`](requirements-frida-tools.txt) in a separate
virtual environment.

## Run

```powershell
uv run python server.py
```

By default the server reads definitions from `.\api-monitor-xml`. Override that
only if you keep the API Monitor XML elsewhere:

```powershell
$env:APIMON_XML_ROOT = "C:\path\to\API Monitor\API"
uv run python server.py
```

## Codex Registration

```bash
codex mcp add apimon-frida -- uv run --directory "/path/to/re-skills/skillpacks/windows-api-monitoring/apimon-frida-mcp" python server.py
```

## Example Prompts

- Search for file APIs: `search_definitions("CreateFile", kind="api", module="Kernel32")`
- Describe a signature: `describe_api("Kernel32", "DeviceIoControl")`
- Trace Notepad file APIs:

```json
{
  "command": "notepad.exe",
  "apis": ["Kernel32!CreateFileW", "Kernel32!ReadFile", "Kernel32!WriteFile"],
  "duration": 10,
  "event_limit": 200
}
```

## Tests

```powershell
uv run python -m unittest discover -s tests
```

The live Frida spawn/attach behavior should be smoke-tested on Windows against a
small fixture or `notepad.exe`. The unit tests cover XML parsing, decoding, hook
generation, trace utilities, and FastMCP in-memory tool registration.
