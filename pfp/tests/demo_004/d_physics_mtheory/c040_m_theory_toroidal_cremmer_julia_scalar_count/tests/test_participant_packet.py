"""Tests for C040 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all 8 canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


class TestParticipantPacket(unittest.TestCase):
    """Validates participant artifacts for challenge C040."""

    def test_task_md_exists_and_declares_bounds(self) -> None:
        """TASK.md must exist, declare formulas, schemas, and AuthorityEffect: None without forbidden hype."""
        task_file = PARTICIPANT_DIR / "TASK.md"
        self.assertTrue(task_file.is_file(), "TASK.md must exist in participant_packet")
        content = task_file.read_text(encoding="utf-8")

        self.assertIn("AuthorityEffect: None", content)
        self.assertIn("Tier: T4", content)
        self.assertTrue("cremmer" in content.lower() or "julia" in content.lower())
        self.assertTrue("hodge" in content.lower() or "dual" in content.lower())
        self.assertIn("K_OUT_OF_BOUNDS", content)
        self.assertIn("UNKNOWN", content)

        # Claim hygiene: zero forbidden hype verbs
        forbidden = [
            "proves",
            "guarantees",
            "mathematically verifies",
            "fundamentally",
            "universal",
            "flawless",
            "weaponized",
        ]
        for word in forbidden:
            self.assertNotIn(
                word, content.lower(), f"Forbidden hype verb '{word}' found in TASK.md"
            )

    def test_accounting_json_specifies_tier_t4(self) -> None:
        """accounting.json must declare Tier T4 bounds, $2.00 ceiling, $0.20 target, <= 70B, and zero fallbacks."""
        accounting_file = PARTICIPANT_DIR / "accounting.json"
        self.assertTrue(
            accounting_file.is_file(), "accounting.json must exist in participant_packet"
        )
        data = json.loads(accounting_file.read_text(encoding="utf-8"))
        self.assertEqual(data.get("tier"), "T4")
        self.assertEqual(data.get("cost_ceiling_usd"), 2.00)
        self.assertEqual(data.get("target_cost_usd"), 0.20)
        self.assertEqual(data.get("model_ceiling_parameters"), 70_000_000_000)
        self.assertFalse(data.get("allow_fallbacks"))

    def test_runner_cli_interface(self) -> None:
        """runner.py must execute correctly from CLI on single case."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            example_case = EXAMPLES_DIR / "ex01_scalars_k7_d4.json"
            self.assertTrue(example_case.is_file(), f"Missing example case: {example_case}")

            out_file = Path(tmp_dir) / "output.json"
            cmd = [
                sys.executable,
                str(RUNNER_FILE),
                "--cases",
                str(example_case),
                "--solver",
                str(SOLVER_FILE),
                "--output",
                str(out_file),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, f"runner.py failed: {proc.stderr}")
            self.assertTrue(out_file.is_file(), "Output file not written")

            res_data = json.loads(out_file.read_text(encoding="utf-8"))
            res_obj = res_data[0] if isinstance(res_data, list) else res_data
            self.assertEqual(res_obj.get("status"), "SOLVED")
            self.assertEqual(res_obj.get("k"), 7)
            self.assertEqual(res_obj.get("D"), 4)
            self.assertEqual(res_obj.get("scalars", {}).get("total"), 70)

    def test_runner_cli_directory_input(self) -> None:
        """runner.py must execute across all files when given a directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "all_examples_output.json"
            cmd = [
                sys.executable,
                str(RUNNER_FILE),
                "--cases",
                str(EXAMPLES_DIR),
                "--solver",
                str(SOLVER_FILE),
                "--output",
                str(out_file),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(
                proc.returncode, 0, f"runner.py directory execution failed: {proc.stderr}"
            )
            self.assertTrue(out_file.is_file(), "Directory output file not written")

            res_data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertIsInstance(res_data, list)
            self.assertEqual(
                len(res_data), 8, f"Expected 8 results from examples directory, got {len(res_data)}"
            )

    def test_all_8_examples_valid(self) -> None:
        """All 8 canonical examples must produce expected results when passed to reference solver."""
        example_files = sorted(EXAMPLES_DIR.glob("*.json"), key=lambda p: p.name.encode("utf-8"))
        self.assertEqual(
            len(example_files), 8, f"Expected 8 example files, found {len(example_files)}"
        )

        for ef in example_files:
            data = json.loads(ef.read_text(encoding="utf-8"))
            expected = data.get("expected")
            self.assertIsNotNone(expected, f"Example {ef.name} missing 'expected' field")

            result = solve(data)
            self.assertEqual(
                result.get("status"), expected.get("status"), f"Status mismatch on {ef.name}"
            )

            if expected.get("status") == "SOLVED":
                self.assertEqual(result.get("k"), expected.get("k"), f"k mismatch on {ef.name}")
                self.assertEqual(result.get("D"), expected.get("D"), f"D mismatch on {ef.name}")
                if "scalars" in expected:
                    self.assertEqual(
                        result.get("scalars", {}).get("total"),
                        expected["scalars"]["total"],
                        f"Scalar total mismatch on {ef.name}",
                    )
                if "coset" in expected:
                    self.assertEqual(
                        result.get("coset", {}).get("difference"),
                        expected["coset"]["difference"],
                        f"Coset difference mismatch on {ef.name}",
                    )
                if "branching" in expected:
                    self.assertEqual(
                        result.get("branching"),
                        expected["branching"],
                        f"Branching mismatch on {ef.name}",
                    )
                if "vectors" in expected:
                    self.assertEqual(
                        result.get("vectors", {}).get("total"),
                        expected["vectors"]["total"],
                        f"Vector total mismatch on {ef.name}",
                    )
            else:
                self.assertEqual(
                    result.get("refusal_code"),
                    expected.get("refusal_code"),
                    f"Refusal code mismatch on {ef.name}",
                )


if __name__ == "__main__":
    unittest.main()
