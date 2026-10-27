"""Tests for C038 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all 10 canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


class TestParticipantPacket(unittest.TestCase):
    """Validates participant artifacts for challenge C038."""

    def test_task_md_exists_and_declares_bounds(self) -> None:
        """TASK.md must exist, declare formulas, schemas, and AuthorityEffect: None without forbidden hype."""
        task_file = PARTICIPANT_DIR / "TASK.md"
        self.assertTrue(task_file.is_file(), "TASK.md must exist in participant_packet")
        content = task_file.read_text(encoding="utf-8")
        self.assertIn("AuthorityEffect", content)
        self.assertIn("None", content)
        self.assertTrue("Regge" in content or "deficit" in content)
        self.assertTrue("Gauss-Bonnet" in content or "euler" in content)
        self.assertTrue("Forman" in content or "Wasserstein" in content)
        self.assertIn("OUT_OF_SCOPE", content)
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

    def test_accounting_json_specifies_tier_t2(self) -> None:
        """accounting.json must declare Tier T2 bounds, $0.50 ceiling, $0.05 target, and zero fallbacks."""
        accounting_file = PARTICIPANT_DIR / "accounting.json"
        self.assertTrue(
            accounting_file.is_file(), "accounting.json must exist in participant_packet"
        )
        data = json.loads(accounting_file.read_text(encoding="utf-8"))
        self.assertIn(data.get("tier"), ("T2", "T3"))
        self.assertEqual(data.get("cost_ceiling_usd"), 0.50)
        self.assertEqual(data.get("target_cost_usd"), 0.05)
        self.assertIn(data.get("model_ceiling_parameters"), (70_000_000_000, "70B"))
        self.assertFalse(data.get("allow_fallbacks"))

    def test_runner_cli_interface(self) -> None:
        """runner.py must execute correctly from CLI on single case."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            example_case = EXAMPLES_DIR / "ex01_octahedron.json"
            self.assertTrue(example_case.is_file())

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
            self.assertIsInstance(res_data, list)
            self.assertEqual(len(res_data), 1)
            self.assertEqual(res_data[0].get("status"), "SOLVED")
            self.assertEqual(res_data[0].get("euler"), 2)
            self.assertEqual(res_data[0].get("V"), 6)
            self.assertEqual(res_data[0].get("E"), 12)
            self.assertEqual(res_data[0].get("F"), 8)

    def test_runner_cli_directory_input(self) -> None:
        """runner.py must execute across all files when given a directory path."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "all_output.json"
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
            self.assertEqual(proc.returncode, 0, f"runner.py on dir failed: {proc.stderr}")
            self.assertTrue(out_file.is_file())
            results = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(len(results), 10)

    def test_canonical_examples_match_reference_solver(self) -> None:
        """All 10 canonical example files must execute and produce declared statuses."""
        example_files = sorted(EXAMPLES_DIR.glob("*.json"))
        self.assertEqual(
            len(example_files), 10, f"Expected 10 examples, found {len(example_files)}"
        )

        expected_statuses = {
            "ex01_octahedron.json": "SOLVED",
            "ex02_csaszar_torus.json": "SOLVED",
            "ex03_projective_plane.json": "SOLVED",
            "ex04_pinched_sphere_refusal.json": "OUT_OF_SCOPE",
            "ex05_surface_with_boundary_refusal.json": "OUT_OF_SCOPE",
            "ex06_triangle_with_tail_alpha0.json": "SOLVED",
            "ex07_triangle_with_tail_alpha_half.json": "SOLVED",
            "ex08_star_graph.json": "SOLVED",
            "ex09_cycle_graph.json": "SOLVED",
            "ex10_oversized_surface_refusal.json": "UNKNOWN",
        }

        for ef in example_files:
            case = json.loads(ef.read_text(encoding="utf-8"))
            actual = solve(case)
            exp_status = expected_statuses[ef.name]
            self.assertEqual(
                actual.get("status"), exp_status, f"Status mismatch in {ef.name}: {actual}"
            )

            if exp_status == "SOLVED":
                if case.get("query") == "surface":
                    self.assertIn("euler", actual)
                    self.assertIn("vertex_curvature", actual)
                else:
                    self.assertIn("edges", actual)
                    self.assertIn("forman", actual["edges"][0])
                    self.assertIn("ollivier", actual["edges"][0])
            elif exp_status == "OUT_OF_SCOPE":
                self.assertIn("witness", actual)
            elif exp_status == "UNKNOWN":
                self.assertIn("refusal_code", actual)

    def test_runner_fail_closed_on_missing_file(self) -> None:
        """runner.py must exit non-zero when input path does not exist."""
        cmd = [
            sys.executable,
            str(RUNNER_FILE),
            "--cases",
            "nonexistent_path_xyz.json",
            "--solver",
            str(SOLVER_FILE),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
