from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "api-monitor-xml"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from apimon_frida_mcp.definitions import ApiMonitorDefinitions
from apimon_frida_mcp.hooks import build_hook_specs, generate_trace_script


class HookGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loader = ApiMonitorDefinitions(API_ROOT)
        loader.parse_file("Windows/Kernel32.xml")
        cls.index = loader.index

    def test_hook_spec_uses_w_export_for_charset_neutral_api(self) -> None:
        spec = build_hook_specs(self.index, ["Kernel32!CreateFile"])[0]

        self.assertEqual(spec["logical_api"], "Kernel32.dll!CreateFile")
        self.assertEqual(spec["export_name"], "CreateFileW")
        self.assertEqual(spec["params"][0]["kind"], "string")
        self.assertTrue(spec["params"][0]["wide"])

    def test_hook_script_contains_frida_hooks_and_kernelbase_fallback(self) -> None:
        specs = build_hook_specs(self.index, ["Kernel32!ReadFile"])
        source = generate_trace_script(specs)

        self.assertIn("Interceptor.attach", source)
        self.assertIn("KernelBase.dll", source)
        self.assertIn("ReadFile", source)
        self.assertIn("PostLength", source)


if __name__ == "__main__":
    unittest.main()
