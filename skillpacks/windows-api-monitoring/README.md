# Windows API Monitoring

Skills and tools for tracing Windows API behavior during reverse engineering.

## Contents

- [`apimon-frida-mcp`](apimon-frida-mcp/): a FastMCP server that uses Frida for
  live spawn/attach tracing and API Monitor's XML corpus for older Win32 API
  definitions.

The MCP server is the entrypoint for agent workflows. It is intended to run on
the Windows host or VM that can access the target process with Frida.
