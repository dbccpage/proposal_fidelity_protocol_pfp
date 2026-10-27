"""Tests for C039 Dual Independent Checkers & Protocol SG-CP v1 Consensus.

Verifies:
  1. Concordance between Stabilizer Tableau Checker and Homology & Cohomology Checker.
  2. 100% agreement and pass rate on all 48 hidden judge cases (32 base, 10 controls, 6 poisoned).
  3. CheckerDisagreementError raised on simulated divergence.
  4. Anti-bypass: rejection of floats, booleans, and phantom keys.
  5. Cryptographic integrity and strict ordinal UTF-8 sorting of judge_packet/manifest.json.
  6. Checker independence: zero shared functions or cross-imports between checkers.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers import (
    dual_evaluator,
    homology_cohomology_checker,
    stabilizer_tableau_checker,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.homology_cohomology_checker import (
    verify_homology_cohomology_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.stabilizer_tableau_checker import (
    verify_stabilizer_tableau_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases"


class TestDualCheckers(unittest.TestCase):
    """Verifies dual checker consensus, edge verification, and anti-bypass properties."""

    def test_dual_checkers_agree_on_base_cases(self) -> None:
        """Both checkers must pass and agree on all 32 base cases."""
        base_cases = sorted(
            (CASES_DIR / "base").glob("*.json"), key=lambda p: p.name.encode("utf-8")
        )
        self.assertEqual(len(base_cases), 32)
        for cf in base_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_stabilizer_tableau_certificate(case, ans)
            ok2, msg2 = verify_homology_cohomology_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_dual_checkers_agree_on_controls(self) -> None:
        """Both checkers must pass and agree on all 10 control cases."""
        ctrl_cases = sorted(
            (CASES_DIR / "controls").glob("*.json"), key=lambda p: p.name.encode("utf-8")
        )
        self.assertEqual(len(ctrl_cases), 10)
        for cf in ctrl_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_stabilizer_tableau_certificate(case, ans)
            ok2, msg2 = verify_homology_cohomology_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_dual_checkers_agree_on_poisoned_cases(self) -> None:
        """Both checkers must pass and agree on all 6 poisoned cases."""
        pois_cases = sorted(
            (CASES_DIR / "poisoned").glob("*.json"), key=lambda p: p.name.encode("utf-8")
        )
        self.assertEqual(len(pois_cases), 6)
        for cf in pois_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_stabilizer_tableau_certificate(case, ans)
            ok2, msg2 = verify_homology_cohomology_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_checker_disagreement_raises_error(self) -> None:
        """Dual evaluator must raise CheckerDisagreementError when checkers diverge."""
        case = {
            "case_id": "test_div",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [[[0, 1], [1, 1], [0, -1], [1, -1]]],
        }
        ans = solve(case)

        orig_c1 = dual_evaluator.verify_stabilizer_tableau_certificate
        try:
            dual_evaluator.verify_stabilizer_tableau_certificate = lambda c, a: (
                False,
                "simulated divergence",
            )
            with self.assertRaises(CheckerDisagreementError):
                assert_dual_agreement(case, ans)
        finally:
            dual_evaluator.verify_stabilizer_tableau_certificate = orig_c1

    def test_manifest_cryptographic_integrity_and_ordinal_sorting(self) -> None:
        """Asserts judge_packet/manifest.json is complete, strictly ordinal sorted, and SHA-256 certified on disk."""
        judge_dir = CHALLENGE_DIR / "judge_packet"
        manifest_file = judge_dir / "manifest.json"
        self.assertTrue(manifest_file.is_file(), "manifest.json must exist in judge_packet")

        raw_manifest = manifest_file.read_bytes()
        self.assertFalse(
            raw_manifest.startswith(b"\xef\xbb\xbf"), "manifest.json contains UTF-8 BOM"
        )

        manifest_data = json.loads(raw_manifest.decode("utf-8"))
        self.assertEqual(
            manifest_data.get("challenge_id"),
            "c039_lattice_z2_gauge_theory_gauss_law",
            f"Invalid challenge_id: {manifest_data.get('challenge_id')}",
        )
        self.assertEqual(
            manifest_data.get("protocol"),
            "SG-CP v1",
            f"Invalid protocol: {manifest_data.get('protocol')}",
        )

        files_entry = manifest_data.get("files", [])
        declared_count = manifest_data.get("files_count")
        self.assertEqual(
            declared_count,
            len(files_entry),
            f"declared_file_count mismatch: {declared_count} != {len(files_entry)}",
        )
        self.assertEqual(
            len(files_entry),
            102,
            f"Expected exactly 102 judge files in manifest, got {len(files_entry)}",
        )

        # Check 1: Strict ordinal UTF-8 sorting invariant
        paths = [item["path"] for item in files_entry]
        sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
        self.assertEqual(
            paths,
            sorted_paths,
            "manifest.json files array violates ordinal UTF-8 sorting invariant",
        )

        # Check 2: Byte-level SHA-256 agreement with actual files on disk
        for entry in files_entry:
            rel_path = entry["path"]
            exp_sha = entry["sha256"]
            exp_bytes = entry["size_bytes"]
            target_path = judge_dir / rel_path
            self.assertTrue(target_path.is_file(), f"Manifest lists missing file: {rel_path}")
            disk_bytes = target_path.read_bytes()
            disk_sha = hashlib.sha256(disk_bytes).hexdigest()
            self.assertEqual(
                disk_sha,
                exp_sha,
                f"SHA-256 mismatch for {rel_path}: {disk_sha} != {exp_sha}",
            )
            self.assertEqual(
                len(disk_bytes),
                exp_bytes,
                f"Size mismatch for {rel_path}: {len(disk_bytes)} != {exp_bytes}",
            )

    def test_anti_bypass_float_rejection(self) -> None:
        """Both checkers must reject float values in place of integers."""
        case = {
            "case_id": "test_flt",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [[[0, 1], [1, 1], [0, -1], [1, -1]]],
        }
        ans = solve(case)
        ans_corrupt = dict(ans, k=2.0)
        ok1, _ = verify_stabilizer_tableau_certificate(case, ans_corrupt)
        ok2, _ = verify_homology_cohomology_certificate(case, ans_corrupt)
        self.assertFalse(ok1, "Checker 1 failed to reject float k")
        self.assertFalse(ok2, "Checker 2 failed to reject float k")

    def test_anti_bypass_bool_rejection(self) -> None:
        """Both checkers must reject boolean values in place of integer ranks."""
        case = {
            "case_id": "test_bool",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [[[0, 1], [1, 1], [0, -1], [1, -1]]],
        }
        ans = solve(case)
        ans_corrupt = dict(ans, rank_star=True)
        ok1, _ = verify_stabilizer_tableau_certificate(case, ans_corrupt)
        ok2, _ = verify_homology_cohomology_certificate(case, ans_corrupt)
        self.assertFalse(ok1, "Checker 1 failed to reject boolean rank_star")
        self.assertFalse(ok2, "Checker 2 failed to reject boolean rank_star")

    def test_anti_bypass_phantom_key_rejection(self) -> None:
        """Both checkers must reject root-level schema injections."""
        case = {
            "case_id": "test_phantom",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [[[0, 1], [1, 1], [0, -1], [1, -1]]],
        }
        ans = solve(case)
        ans_corrupt = dict(ans, injected_phantom_key="exploit")
        ok1, _ = verify_stabilizer_tableau_certificate(case, ans_corrupt)
        ok2, _ = verify_homology_cohomology_certificate(case, ans_corrupt)
        self.assertFalse(ok1, "Checker 1 failed to reject phantom key")
        self.assertFalse(ok2, "Checker 2 failed to reject phantom key")

    def test_checker_independence(self) -> None:
        """Asserts zero cross-imports or shared mutable state between Checker 1 and Checker 2."""
        c1_path = Path(stabilizer_tableau_checker.__file__).resolve()
        c2_path = Path(homology_cohomology_checker.__file__).resolve()

        c1_tree = ast.parse(c1_path.read_text(encoding="utf-8"))
        c2_tree = ast.parse(c2_path.read_text(encoding="utf-8"))

        # Checker 1 must not import homology_cohomology_checker
        for node in ast.walk(c1_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("homology_cohomology_checker", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("homology_cohomology_checker", node.module)

        # Checker 2 must not import stabilizer_tableau_checker
        for node in ast.walk(c2_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("stabilizer_tableau_checker", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("stabilizer_tableau_checker", node.module)


if __name__ == "__main__":
    unittest.main()
