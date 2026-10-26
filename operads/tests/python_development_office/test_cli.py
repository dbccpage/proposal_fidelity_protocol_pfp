"""Unit tests for python_development_office CLI entrypoint."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omega_engine_operads.frontend.cli.python_dev_cli import main as run_cli


class TestCLI(unittest.TestCase):
    def test_cli_json_output_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "bad.py"
            file_path.write_text("def f(items=[]):\n    pass\n", encoding="utf-8")

            stdout_capture = io.StringIO()
            with patch("sys.stdout", stdout_capture):
                exit_code = run_cli([str(file_path), "--json"])

            self.assertEqual(exit_code, 1)
            output_str = stdout_capture.getvalue()
            data = json.loads(output_str)

            self.assertEqual(data["schema"], "omega.python_development_office.v1")
            self.assertEqual(data["total_findings"], 1)
            self.assertEqual(data["findings"][0]["rule_code"], "MUTABLE_DEFAULT_ARG")

    def test_cli_clean_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "good.py"
            file_path.write_text(
                "def f(items=None):\n    items = items or []\n",
                encoding="utf-8",
            )

            stdout_capture = io.StringIO()
            with patch("sys.stdout", stdout_capture):
                exit_code = run_cli([str(file_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn("No findings detected", stdout_capture.getvalue())


if __name__ == "__main__":
    unittest.main()
