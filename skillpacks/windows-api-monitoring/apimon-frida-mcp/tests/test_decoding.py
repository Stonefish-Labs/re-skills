from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "api-monitor-xml"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from apimon_frida_mcp.decoding import classify_param, decode_named_value, enrich_event
from apimon_frida_mcp.definitions import ApiMonitorDefinitions


class DecodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loader = ApiMonitorDefinitions(API_ROOT)
        loader.parse_file("Windows/Kernel32.xml")
        cls.index = loader.index

    def test_lpctstr_is_classified_as_a_wide_string_for_w_alias(self) -> None:
        api = self.index.require_api("Kernel32!CreateFileW")

        classified = classify_param(self.index, api, api.params[0], 0, api_name="CreateFileW")

        self.assertEqual(classified["kind"], "string")
        self.assertTrue(classified["wide"])

    def test_named_enum_and_flags_are_decoded(self) -> None:
        enum_type = self.index.resolve_type("[CreationDisposition]")
        flag_type = self.index.resolve_type("[FILE_ACCESS_MASK]")

        self.assertEqual(decode_named_value(enum_type, 3)["name"], "OPEN_EXISTING")
        decoded_flags = decode_named_value(flag_type, 0x00120089)
        self.assertIn("FILE_GENERIC_READ", decoded_flags["names"])

    def test_enrich_event_adds_signature_success_and_decoded_arguments(self) -> None:
        event = {
            "api": "Kernel32.dll!CreateFile",
            "module": "Kernel32.dll",
            "return_value": "0x44",
            "args": [
                {"name": "lpFileName", "value": "C:\\\\temp\\\\x.txt"},
                {"name": "dwDesiredAccess", "value": 0x00120089},
                {"name": "dwShareMode", "value": 0},
                {"name": "lpSecurityAttributes", "value": "0x0"},
                {"name": "dwCreationDisposition", "value": 3},
                {"name": "dwFlagsAndAttributes", "value": 0x80},
                {"name": "hTemplateFile", "value": "0x0"},
            ],
        }

        enriched = enrich_event(self.index, event)

        self.assertIn("CreateFile", enriched["signature"])
        self.assertIn("decoded", enriched["args"][1])
        self.assertEqual(enriched["args"][4]["decoded"]["name"], "OPEN_EXISTING")


if __name__ == "__main__":
    unittest.main()
