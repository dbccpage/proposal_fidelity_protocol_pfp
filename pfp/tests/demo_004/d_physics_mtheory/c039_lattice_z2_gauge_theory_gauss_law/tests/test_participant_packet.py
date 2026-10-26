"""Tests for C039 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all 10 canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


class TestParticipantPacket(unittest.TestCase):
    """Validates participant artifacts for challenge C039."""

    def test_task_md_exists_and_declares_bounds(self) -> None:
        """TASK.md must exist, declare formulas, schemas, and AuthorityEffect: None without forbidden hype."""
        task_file = PARTICIPANT_DIR / "TASK.md"
        self.assertTrue(task_file.is_file(), "TASK.md must exist in participant_packet")
        content = task_file.read_text(encoding="utf-8")
        self.assertIn("AuthorityEffect", content)
        self.assertIn("None", content)
        self.assertTrue("z2" in content.lower() or "gauge" in content.lower())
        self.assertTrue("gauss" in content.lower() or "star" in content.lower())
        self.assertTrue("plaquette" in content.lower() or "flux" in content.lower())
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

    def test_accounting_json_specifies_tier_t3(self) -> None:
        """accounting.json must declare Tier T3 bounds, $1.00 ceiling, $0.10 target, and zero fallbacks."""
        accounting_file = PARTICIPANT_DIR / "accounting.json"
        self.assertTrue(
            accounting_file.is_file(), "accounting.json must exist in participant_packet"
        )
        data = json.loads(accounting_file.read_text(encoding="utf-8"))
        self.assertEqual(data.get("tier"), "T3")
        self.assertEqual(data.get("cost_ceiling_usd"), 1.00)
        self.assertEqual(data.get("target_cost_usd"), 0.10)
        self.assertIn(data.get("model_ceiling_parameters"), (70_000_000_000, "70B"))
        self.assertFalse(data.get("allow_fallbacks"))

    def test_runner_cli_interface(self) -> None:
        """runner.py must execute correctly from CLI on single case."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            example_case = EXAMPLES_DIR / "ex01_sphere_tetrahedron.json"
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
            self.assertEqual(res_obj.get("k"), 0)
            self.assertEqual(res_obj.get("gsd"), 1)
            self.assertEqual(res_obj.get("V"), 4)
            self.assertEqual(res_obj.get("E"), 6)
            self.assertEqual(res_obj.get("F"), 4)

    def test_runner_cli_directory_input(self) -> None:
        """runner.py must execute across all files when given a directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "output_all.json"
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
            self.assertEqual(proc.returncode, 0, f"runner.py directory mode failed: {proc.stderr}")
            self.assertTrue(out_file.is_file(), "Output file not written")

            res_data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertIsInstance(res_data, list)
            self.assertEqual(len(res_data), 10, f"Expected 10 results, got {len(res_data)}")

    def test_all_10_examples_valid(self) -> None:
        """Validates all 10 canonical examples against reference solver."""
        expected_statuses = {
            "ex01_sphere_tetrahedron.json": "SOLVED",
            "ex02_torus_one_vertex.json": "SOLVED",
            "ex03_torus_2x2_square.json": "SOLVED",
            "ex04_projective_plane_rp2.json": "SOLVED",
            "ex05_klein_bottle.json": "SOLVED",
            "ex06_genus2_double_torus.json": "SOLVED",
            "ex07_sector_even_charges.json": "SOLVED",
            "ex08_sector_odd_charges.json": "SOLVED",
            "ex09_non_manifold_pinch.json": "OUT_OF_SCOPE",
            "ex10_oversized_complex.json": "UNKNOWN",
        }

        for fname, exp_status in expected_statuses.items():
            fpath = EXAMPLES_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing example file: {fname}")
            case_data = json.loads(fpath.read_text(encoding="utf-8"))
            result = solve(case_data)
            self.assertEqual(
                result.get("status"),
                exp_status,
                f"Status mismatch on {fname}: expected {exp_status}, got {result.get('status')}",
            )


if __name__ == "__main__":
    unittest.main()
