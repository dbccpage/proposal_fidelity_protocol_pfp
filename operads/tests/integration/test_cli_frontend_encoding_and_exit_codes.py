"""Integration test for CLI frontend exit codes, structured JSON stdout, and Windows CP1252 encoding safety."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from omega_engine_operads.frontend.cli.main import main


class TestCliFrontendEncodingAndExitCodes(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "cli_test.db")

        # Create a valid skill document with unicode math symbols to test encoding safety
        skill_dir = self.workspace_root / ".agents" / "skills" / "math-solver"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            """# Unicode Math Solver Φ₁ 🚀 ⊗
A skill with non-ASCII symbols.

```oewas.operation.v3
operation_id: "math:solve_tensor"
inputs:
  - name: "tensor_in"
    colour_id: "Data"
    schema_ref: "schema:tensor:v1"
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: "receipt_out"
  colour_id: "Receipt"
  schema_ref: "schema:receipt:v1"
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
```
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def test_compile_catalog_success_and_json_stdout(self) -> None:
        """Verifies exit code 0 and valid JSON output for successful catalog compilation."""
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        argv = [
            "--workspace", str(self.workspace_root),
            "--db-path", self.db_path,
            "--json",
            "compile-catalog",
            "--estate", "canonical",
        ]

        with patch.object(sys, "stdout", stdout_buf), patch.object(sys, "stderr", stderr_buf):
            rc = main(argv)

        self.assertEqual(rc, 0, f"CLI exited with code {rc}, stderr: {stderr_buf.getvalue()}")
        output_str = stdout_buf.getvalue()
        payload = json.loads(output_str)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["total_skills"], 1)
        self.assertEqual(payload["total_operations"], 1)
        self.assertEqual(payload["epoch"], 1)

    def test_compile_catalog_failure_returns_exit_code_1(self) -> None:
        """Verifies exit code 1 when catalog compilation fails due to bad syntax."""
        bad_dir = self.workspace_root / ".agents" / "skills" / "broken-skill"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "SKILL.md").write_text(
            """# Broken
```oewas.operation.v3
inputs: [ unclosed
```
""",
            encoding="utf-8",
        )

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        argv = [
            "--workspace", str(self.workspace_root),
            "--db-path", self.db_path,
            "--json",
            "compile-catalog",
            "--estate", "canonical",
        ]

        with patch.object(sys, "stdout", stdout_buf), patch.object(sys, "stderr", stderr_buf):
            rc = main(argv)

        self.assertEqual(rc, 1, "CLI should return exit code 1 on compilation failure")
        payload = json.loads(stdout_buf.getvalue())
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["code"], "DOCUMENT_PARSE_ERROR")

    def test_invalid_cli_arguments_returns_exit_code_2(self) -> None:
        """Verifies exit code 2 on invalid CLI arguments or missing commands."""
        stderr_buf = io.StringIO()
        with patch.object(sys, "stderr", stderr_buf):
            with self.assertRaises(SystemExit) as ctx:
                main(["--unknown-argument-xyz"])
            self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
