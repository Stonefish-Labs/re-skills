from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from apimon_frida_mcp.config import DROPIN_XML_DIR, discover_xml_root


class ConfigTests(unittest.TestCase):
    def test_default_xml_root_is_repo_dropin_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.assertEqual(discover_xml_root(root, env={}), (root / DROPIN_XML_DIR).resolve())

    def test_nested_api_folder_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / DROPIN_XML_DIR / "API"
            (nested / "Windows").mkdir(parents=True)

            self.assertEqual(discover_xml_root(root, env={}), nested.resolve())

    def test_env_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            xml_root = Path(tmp) / "external-api"
            (xml_root / "Headers").mkdir(parents=True)

            self.assertEqual(discover_xml_root(PROJECT_ROOT, env={"APIMON_XML_ROOT": str(xml_root)}), xml_root.resolve())


if __name__ == "__main__":
    unittest.main()
