from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from apimon_frida_mcp.tracer import split_command


class TracerUtilityTests(unittest.TestCase):
    def test_split_command_handles_quoted_paths(self) -> None:
        self.assertEqual(split_command('"C:\\Program Files\\App\\app.exe" --flag value'), ["C:\\Program Files\\App\\app.exe", "--flag", "value"])


if __name__ == "__main__":
    unittest.main()
