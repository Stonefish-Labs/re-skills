from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "api-monitor-xml"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from apimon_frida_mcp.definitions import ApiMonitorDefinitions


class DefinitionParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loader = ApiMonitorDefinitions(API_ROOT)
        loader.parse_file("Windows/Kernel32.xml")
        cls.index = loader.index

    def test_charset_alias_resolves_createfilew(self) -> None:
        api = self.index.find_api("Kernel32!CreateFileW")

        self.assertIsNotNone(api)
        self.assertEqual(api.name, "CreateFile")
        self.assertTrue(api.both_charset)
        self.assertEqual(api.params[0].type, "LPCTSTR")

    def test_buffer_hints_are_preserved_for_file_and_ioctl_calls(self) -> None:
        read_file = self.index.require_api("Kernel32!ReadFile")
        read_params = {param.name: param for param in read_file.params}
        self.assertEqual(read_params["lpBuffer"].attr("PostLength"), "lpNumberOfBytesRead")

        ioctl = self.index.require_api("Kernel32!DeviceIoControl")
        ioctl_params = {param.name: param for param in ioctl.params}
        self.assertEqual(ioctl_params["lpInBuffer"].attr("Length"), "nInBufferSize")
        self.assertEqual(ioctl_params["lpOutBuffer"].attr("PostLength"), "lpBytesReturned")

    def test_bracketed_aliases_decode_enums_and_flags(self) -> None:
        creation = self.index.resolve_type("CreationDisposition")
        self.assertIsNotNone(creation)
        self.assertEqual(creation.enum[3], "OPEN_EXISTING")

        access = self.index.resolve_type("[FILE_ACCESS_MASK]")
        self.assertIsNotNone(access)
        self.assertIn(0x00120089, access.flags)
        self.assertEqual(access.flags[0x00120089], "FILE_GENERIC_READ")

    def test_search_matches_flag_set_names(self) -> None:
        results = self.index.search("FILE_GENERIC_READ", kind="flags", limit=10)

        self.assertTrue(any(result.name == "[FILE_ACCESS_MASK]" for result in results))


if __name__ == "__main__":
    unittest.main()
