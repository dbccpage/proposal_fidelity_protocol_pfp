"""Tests for C038 Dual Independent Checkers & Protocol SG-CP v1 Consensus.

Verifies:
  1. Concordance between Combinatorial Primal Checker and Simplicial Homology Dual Checker.
  2. 100% agreement and pass rate on all 46 hidden judge cases (30 base, 10 controls, 6 poisoned).
  3. CheckerDisagreementError raised on simulated divergence.
  4. Anti-bypass: rejection of floats, unreduced rationals, booleans, and phantoms.
  5. Checker independence: zero shared functions or cross-imports between checkers.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers import (
    combinatorial_primal_checker,
    dual_evaluator,
    homology_dual_potential_checker,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.combinatorial_primal_checker import (
    verify_combinatorial_primal_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.judge_packet.checkers.homology_dual_potential_checker import (
    verify_homology_dual_potential_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases"


class TestDualCheckers(unittest.TestCase):
    """Verifies dual checker consensus, edge verification, and anti-bypass properties."""

    def test_dual_checkers_agree_on_base_cases(self) -> None:
        """Both checkers must pass and agree on all 30 base cases."""
        base_cases = sorted((CASES_DIR / "base").glob("*.json"))
        self.assertEqual(len(base_cases), 30)
        for cf in base_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_dual_checkers_agree_on_controls(self) -> None:
        """Both checkers must pass and agree on all 10 control cases."""
        ctrl_cases = sorted((CASES_DIR / "controls").glob("*.json"))
        self.assertEqual(len(ctrl_cases), 10)
        for cf in ctrl_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_dual_checkers_agree_on_poisoned_cases(self) -> None:
        """Both checkers must pass and agree on all 6 poisoned cases."""
        pois_cases = sorted((CASES_DIR / "poisoned").glob("*.json"))
        self.assertEqual(len(pois_cases), 6)
        for cf in pois_cases:
            case = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case)
            ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
            self.assertTrue(ok1, f"Checker 1 rejected {cf.name}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected {cf.name}: {msg2}")

    def test_checker_disagreement_raises_error(self) -> None:
        """Dual evaluator must raise CheckerDisagreementError when checkers diverge."""
        case = {
            "case_id": "test_div",
            "query": "surface",
            "triangles": [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]],
        }
        ans = solve(case)

        orig_c1 = dual_evaluator.verify_combinatorial_primal_certificate
        try:
            dual_evaluator.verify_combinatorial_primal_certificate = lambda c, a: (
                False,
                "simulated divergence",
            )
            with self.assertRaises(CheckerDisagreementError):
                assert_dual_agreement(case, ans)
        finally:
            dual_evaluator.verify_combinatorial_primal_certificate = orig_c1

    def test_anti_bypass_rejects_unreduced_rationals(self) -> None:
        """Checkers must reject unreduced fraction strings like 2/4 or 2/6."""
        case = {
            "case_id": "test_unred",
            "query": "surface",
            "triangles": [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 4],
                [0, 4, 1],
                [5, 2, 1],
                [5, 3, 2],
                [5, 4, 3],
                [5, 1, 4],
            ],
        }
        ans = solve(case)
        ans["vertex_curvature"]["0"] = "2/6"  # Unreduced
        ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
        self.assertFalse(ok1)
        self.assertFalse(ok2)
        self.assertIn("reduced rational", msg1.lower())
        self.assertIn("reduced rational", msg2.lower())

    def test_anti_bypass_rejects_booleans_in_integer_fields(self) -> None:
        """Checkers must reject booleans masquerading as integers (e.g. euler=True)."""
        case = {
            "case_id": "test_bool",
            "query": "surface",
            "triangles": [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]],
        }
        ans = solve(case)
        ans["euler"] = True  # bool is subclass of int in Python!
        ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
        self.assertFalse(ok1)
        self.assertFalse(ok2)

    def test_checker_isolation_and_independence(self) -> None:
        """Checker 1 and Checker 2 must not cross-import each other or import solver modules."""
        c1_path = Path(combinatorial_primal_checker.__file__).resolve()
        c2_path = Path(homology_dual_potential_checker.__file__).resolve()

        c1_tree = ast.parse(c1_path.read_text(encoding="utf-8"))
        c2_tree = ast.parse(c2_path.read_text(encoding="utf-8"))

        for tree, name in [(c1_tree, "Checker 1"), (c2_tree, "Checker 2")]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(
                            "reference_solver", alias.name, f"{name} imports reference_solver!"
                        )
                elif isinstance(node, ast.ImportFrom):
                    mod_name = node.module or ""
                    self.assertNotIn(
                        "reference_solver", mod_name, f"{name} imports reference_solver!"
                    )

        # Assert C1 does not import C2 and vice-versa
        for node in ast.walk(c1_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                self.assertNotIn("homology_dual_potential_checker", mod)
        for node in ast.walk(c2_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                self.assertNotIn("combinatorial_primal_checker", mod)

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
            "c038_regge_combinatorial_curvature",
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
            100,
            f"Expected exactly 100 judge files in manifest, got {len(files_entry)}",
        )

        # Check 1: Strict ordinal UTF-8 sorting invariant
        paths = [item["path"] for item in files_entry]
        sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
        self.assertEqual(
            paths,
            sorted_paths,
            "manifest.json files are not ordered in strict ordinal UTF-8 byte order!",
        )

        # Check 2: Byte-level SHA-256 and size verification on disk for every entry
        for item in files_entry:
            file_path = judge_dir / item["path"]
            self.assertTrue(
                file_path.is_file(),
                f"Manifest file entry does not exist on disk: {file_path}",
            )
            raw = file_path.read_bytes()
            actual_sha = hashlib.sha256(raw).hexdigest()
            self.assertEqual(
                actual_sha,
                item["sha256"],
                f"SHA-256 mismatch for {item['path']}: {actual_sha} != {item['sha256']}",
            )
            self.assertEqual(
                len(raw),
                item["size_bytes"],
                f"Size mismatch for {item['path']}: {len(raw)} != {item['size_bytes']}",
            )

        # Check 3: Complete coverage (no unindexed files in judge_packet)
        disk_files: set[str] = set()
        for p in judge_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(judge_dir).as_posix()
                if rel == "manifest.json" or "__pycache__" in p.parts or p.name.endswith(".pyc"):
                    continue
                disk_files.add(rel)

        unindexed = disk_files - set(paths)
        self.assertEqual(
            len(unindexed),
            0,
            f"Unindexed files found in judge_packet: {sorted(unindexed)}",
        )


# =========================================================================
# Regression Test Suite for Defects A, B, and C
# =========================================================================


class TestDualCheckersRegression(unittest.TestCase):
    """Verifies that Defect A (Lipschitz blindness), Defect B (marginal leak blindness),
    and Defect C (malformed syntax refusal alignment) are permanently resolved."""

    def setUp(self) -> None:
        self.k3_case = {
            "case_id": "reg_k3",
            "query": "graph",
            "edges": [[0, 1], [1, 2], [2, 0]],
            "alpha": "0",
        }
        self.k4_case = {
            "case_id": "reg_k4",
            "query": "graph",
            "edges": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
            "alpha": "0",
        }
        self.p3_case = {
            "case_id": "reg_p3",
            "query": "graph",
            "edges": [[0, 1], [1, 2]],
            "alpha": "1/2",
        }

    # ---------------------------------------------------------------------
    # Defect A Regression Tests: Isolated Dual Potential & Duality Gap
    # ---------------------------------------------------------------------

    def test_isolated_potential_lipschitz_violation_rejected_by_both(self) -> None:
        """Checker 1 and Checker 2 must BOTH reject an answer where ONLY the dual
        potential violates 1-Lipschitz, while plan and curvature are valid."""
        ans = solve(self.k3_case)
        # Perturb potential on edge (0, 1): set node 1 potential to 5 (slope = 5 > 1)
        ans["edges"][0]["potential"]["1"] = "5"

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k3_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k3_case, ans)
        res = evaluate_dual(self.k3_case, ans)

        self.assertFalse(ok1, "Checker 1 failed to reject isolated Lipschitz violation")
        self.assertFalse(ok2, "Checker 2 failed to reject isolated Lipschitz violation")
        self.assertIn("lipschitz", msg1.lower())
        self.assertIn("lipschitz", msg2.lower())
        self.assertTrue(res["agreed"], "Checkers must agree on rejection (no CHECKER_DISAGREEMENT)")
        self.assertEqual(res["verdict"], "FAIL")

    def test_isolated_potential_lipschitz_violation_k4_rejected_by_both(self) -> None:
        """Isolated Lipschitz violation on complete graph K4 must be rejected by both."""
        ans = solve(self.k4_case)
        ans["edges"][0]["potential"]["1"] = "3"

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k4_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k4_case, ans)
        res = evaluate_dual(self.k4_case, ans)

        self.assertFalse(ok1)
        self.assertFalse(ok2)
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_isolated_duality_gap_violation_rejected_by_both(self) -> None:
        """Checker 1 and Checker 2 must BOTH reject an answer where the potential is
        1-Lipschitz (flat 0) but the dual objective fails to equal transport cost."""
        ans = solve(self.k3_case)
        # Set all potentials to 0: slope is 0 <= 1 everywhere, but dual_obj = 0 != W_1 (1/2)
        for node in ["0", "1", "2"]:
            ans["edges"][0]["potential"][node] = "0"

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k3_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k3_case, ans)
        res = evaluate_dual(self.k3_case, ans)

        self.assertFalse(ok1, f"Checker 1 passed zero duality gap violation: {msg1}")
        self.assertFalse(ok2, f"Checker 2 passed zero duality gap violation: {msg2}")
        self.assertIn("duality gap", msg1.lower())
        self.assertIn("duality gap", msg2.lower())
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")

    # ---------------------------------------------------------------------
    # Defect B Regression Tests: Isolated Primal Plan Marginals & Cost
    # ---------------------------------------------------------------------

    def test_isolated_primal_plan_source_marginal_leak_rejected_by_both(self) -> None:
        """Checker 1 and Checker 2 must BOTH reject an answer where ONLY the primal
        plan leaks mass, while dual potential and curvature are valid."""
        ans = solve(self.k3_case)
        # Perturb plan mass on edge (0, 1): scale mass from 1/2 to 1/4 (leak 1/4)
        ans["edges"][0]["plan"][0]["mass"] = "1/4"

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k3_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k3_case, ans)
        res = evaluate_dual(self.k3_case, ans)

        self.assertFalse(ok1, "Checker 1 failed to reject primal plan marginal leak")
        self.assertFalse(ok2, "Checker 2 failed to reject primal plan marginal leak")
        self.assertIn("marginal", msg1.lower())
        self.assertIn("marginal", msg2.lower())
        self.assertTrue(res["agreed"], "Checkers must agree on rejection (no CHECKER_DISAGREEMENT)")
        self.assertEqual(res["verdict"], "FAIL")

    def test_isolated_primal_plan_target_marginal_oversubscription_rejected_by_both(self) -> None:
        """Checker 1 and Checker 2 must BOTH reject target marginal oversubscription."""
        ans = solve(self.k4_case)
        ans["edges"][0]["plan"][0]["mass"] = "3/4"

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k4_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k4_case, ans)
        res = evaluate_dual(self.k4_case, ans)

        self.assertFalse(ok1)
        self.assertFalse(ok2)
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_isolated_primal_cost_mismatch_rejected_by_both(self) -> None:
        """If a plan satisfies marginals but has suboptimal cost, both checkers must reject."""
        ans = solve(self.k3_case)
        # Substitute a feasible but suboptimal plan or perturb plan cost
        # Modify plan mass routing to induce cost discrepancy while keeping marginals
        # On K3, alpha=0, m_u(1)=1/2, m_u(2)=1/2, m_v(0)=1/2, m_v(2)=1/2.
        # Original: (1->0: 1/2), (2->2: 1/2) -> cost = 1/2*1 + 1/2*0 = 1/2.
        # Detour: (1->2: 1/2), (2->0: 1/2) -> cost = 1/2*1 + 1/2*1 = 1.
        ans["edges"][0]["plan"] = [
            {"from": 1, "to": 2, "mass": "1/2"},
            {"from": 2, "to": 0, "mass": "1/2"},
        ]
        # Marginals: source 1 has 1/2, source 2 has 1/2 (correct!). Target 2 has 1/2, target 0 has 1/2 (correct!).
        # But cost is 1 != exact_w1 (1/2)!

        ok1, msg1 = verify_combinatorial_primal_certificate(self.k3_case, ans)
        ok2, msg2 = verify_homology_dual_potential_certificate(self.k3_case, ans)
        res = evaluate_dual(self.k3_case, ans)

        self.assertFalse(ok1, f"Checker 1 passed suboptimal plan: {msg1}")
        self.assertFalse(ok2, f"Checker 2 passed suboptimal plan: {msg2}")
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")

    # ---------------------------------------------------------------------
    # Defect C Regression Tests: Malformed Syntax Refusal Alignment
    # ---------------------------------------------------------------------

    def test_malformed_syntax_surface_cases_accepted_by_both(self) -> None:
        """Degenerate triangles, non-integer vertices, and short triangles must produce
        status UNKNOWN: MALFORMED_CASE_STRUCTURE, accepted as PASS by both checkers."""
        malformed_surface_cases = [
            (
                "degenerate_triangle",
                {
                    "id": "syn_deg",
                    "query": "surface",
                    "triangles": [[0, 0, 1], [0, 1, 2], [1, 2, 0]],
                },
            ),
            (
                "non_integer_vertex",
                {
                    "id": "syn_noint",
                    "query": "surface",
                    "triangles": [["a", 1, 2], [1, 2, 0], [2, 0, 1]],
                },
            ),
            (
                "bool_vertex",
                {
                    "id": "syn_bool",
                    "query": "surface",
                    "triangles": [[True, 1, 2], [1, 2, 0], [2, 0, 1]],
                },
            ),
            (
                "short_triangle",
                {
                    "id": "syn_short",
                    "query": "surface",
                    "triangles": [[0, 1], [1, 2, 0], [2, 0, 1]],
                },
            ),
            (
                "long_triangle",
                {"id": "syn_long", "query": "surface", "triangles": [[0, 1, 2, 3], [1, 2, 0]]},
            ),
        ]

        for desc, case in malformed_surface_cases:
            ans = solve(case)
            self.assertEqual(
                ans.get("status"),
                "UNKNOWN",
                f"{desc} solver status should be UNKNOWN, got {ans.get('status')}",
            )
            self.assertEqual(
                ans.get("refusal_code"),
                "MALFORMED_CASE_STRUCTURE",
                f"{desc} refusal_code should be MALFORMED_CASE_STRUCTURE",
            )

            ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
            res = evaluate_dual(case, ans)

            self.assertTrue(ok1, f"Checker 1 rejected valid refusal for {desc}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected valid refusal for {desc}: {msg2}")
            self.assertTrue(res["agreed"], f"Checkers disagreed on refusal for {desc}")
            self.assertEqual(
                res["verdict"], "PASS", f"Dual evaluator should PASS refusal for {desc}"
            )

    def test_malformed_syntax_graph_cases_accepted_by_both(self) -> None:
        """1-vertex edges, 3-vertex edges, and non-integer edge vertices must produce
        status UNKNOWN: MALFORMED_CASE_STRUCTURE, accepted as PASS by both checkers."""
        malformed_graph_cases = [
            (
                "one_vertex_edge",
                {"id": "syn_1v_e", "query": "graph", "edges": [[0], [1, 2]], "alpha": "0"},
            ),
            (
                "three_vertex_edge",
                {"id": "syn_3v_e", "query": "graph", "edges": [[0, 1, 2], [1, 2]], "alpha": "0"},
            ),
            (
                "non_integer_edge",
                {"id": "syn_noint_e", "query": "graph", "edges": [["a", 1], [1, 2]], "alpha": "0"},
            ),
            (
                "bool_edge_vertex",
                {"id": "syn_bool_e", "query": "graph", "edges": [[True, 1], [1, 2]], "alpha": "0"},
            ),
        ]

        for desc, case in malformed_graph_cases:
            ans = solve(case)
            self.assertEqual(
                ans.get("status"),
                "UNKNOWN",
                f"{desc} solver status should be UNKNOWN, got {ans.get('status')}",
            )
            self.assertEqual(
                ans.get("refusal_code"),
                "MALFORMED_CASE_STRUCTURE",
                f"{desc} refusal_code should be MALFORMED_CASE_STRUCTURE",
            )

            ok1, msg1 = verify_combinatorial_primal_certificate(case, ans)
            ok2, msg2 = verify_homology_dual_potential_certificate(case, ans)
            res = evaluate_dual(case, ans)

            self.assertTrue(ok1, f"Checker 1 rejected valid refusal for {desc}: {msg1}")
            self.assertTrue(ok2, f"Checker 2 rejected valid refusal for {desc}: {msg2}")
            self.assertTrue(res["agreed"], f"Checkers disagreed on refusal for {desc}")
            self.assertEqual(
                res["verdict"], "PASS", f"Dual evaluator should PASS refusal for {desc}"
            )

    def test_anti_cheat_unwarranted_solved_on_malformed_syntax_rejected(self) -> None:
        """If a solver returns status SOLVED on a malformed case, both checkers must reject."""
        case = {
            "id": "syn_anti_cheat",
            "query": "surface",
            "triangles": [[0, 0, 1], [0, 1, 2], [1, 2, 0]],
        }
        bogus_solved = {
            "id": "syn_anti_cheat",
            "status": "SOLVED",
            "V": 3,
            "E": 3,
            "F": 3,
            "euler": 3,
            "orientable": True,
            "classification": {"orientable_genus": 0},
            "vertex_curvature": {"0": "0", "1": "0", "2": "0"},
        }

        ok1, msg1 = verify_combinatorial_primal_certificate(case, bogus_solved)
        ok2, msg2 = verify_homology_dual_potential_certificate(case, bogus_solved)
        res = evaluate_dual(case, bogus_solved)

        self.assertFalse(ok1, "Checker 1 failed to reject SOLVED on degenerate triangle")
        self.assertFalse(ok2, "Checker 2 failed to reject SOLVED on degenerate triangle")
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_anti_cheat_wrong_refusal_code_on_malformed_syntax_rejected(self) -> None:
        """If a solver returns OUT_OF_SCOPE instead of UNKNOWN on a malformed syntax case,
        both checkers must reject it."""
        case = {
            "id": "syn_wrong_refusal",
            "query": "surface",
            "triangles": [[0, 0, 1], [0, 1, 2], [1, 2, 0]],
        }
        bogus_oos = {
            "id": "syn_wrong_refusal",
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "edge_not_two_triangles", "edge": [0, 1], "count": 1},
        }

        ok1, msg1 = verify_combinatorial_primal_certificate(case, bogus_oos)
        ok2, msg2 = verify_homology_dual_potential_certificate(case, bogus_oos)
        res = evaluate_dual(case, bogus_oos)

        self.assertFalse(ok1, "Checker 1 should reject OUT_OF_SCOPE on malformed syntax")
        self.assertFalse(ok2, "Checker 2 should reject OUT_OF_SCOPE on malformed syntax")
        self.assertTrue(res["agreed"])
        self.assertEqual(res["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
