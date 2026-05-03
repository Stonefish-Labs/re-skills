from __future__ import annotations

import importlib.util
import asyncio
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@unittest.skipUnless(importlib.util.find_spec("fastmcp"), "fastmcp is not installed in this environment")
class FastMCPInMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_tools_are_registered_and_search_returns_text(self) -> None:
        asyncio.get_running_loop().slow_callback_duration = 10.0
        os.environ["APIMON_XML_ROOT"] = str(PROJECT_ROOT / "api-monitor-xml")
        from fastmcp.client import Client
        from server import mcp

        async with Client(transport=mcp) as client:
            tools = await client.list_tools()
            self.assertIn("search_definitions", {tool.name for tool in tools})

            result = await client.call_tool(
                "search_definitions",
                {"query": "CreateFile", "kind": "api", "module": "Kernel32", "limit": 5},
            )
            text = result.content[0].text
            self.assertIn("CreateFile", text)


if __name__ == "__main__":
    unittest.main()
