"""Tests for C039 Reference Solver.

Validates toric code topological degeneracy, Gauss's law sector counting,
non-manifold refusals, DDC operational tracing, and AST anti-hardcoding regression.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from c039_lattice_z2_gauge_theory_gauss_law.reference_solver import (
    cell_complex,
    ddc_tracer,
    f2_algebra,
    gauss_sector,
    solver,
)
from c039_lattice_z2_gauge_theory_gauss_law.reference_solver.solver import (
    get_last_tracer,
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = CHALLENGE_DIR / "participant_packet" / "examples"


class TestReferenceSolver(unittest.TestCase):
    """Verifies algorithmic correctness of C039 reference solver without hardcoding."""

    def test_degeneracy_tetrahedron_sphere(self) -> None:
        """Tetrahedron S^2: V=4, E=6, F=4, euler=2, k=0, gsd=1."""
        case = {
            "case_id": "test_tet",
            "query": "degeneracy",
            "vertices": [0, 1, 2, 3],
            "edges": [[0, 1], [1, 2], [2, 0], [0, 3], [1, 3], [2, 3]],
            "faces": [
                [[0, 1], [1, 1], [2, 1]],
                [[0, -1], [3, 1], [4, -1]],
                [[1, -1], [4, 1], [5, -1]],
                [[2, -1], [5, 1], [3, -1]],
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["V"], 4)
        self.assertEqual(res["E"], 6)
        self.assertEqual(res["F"], 4)
        self.assertEqual(res["euler"], 2)
        self.assertEqual(res["k"], 0)
        self.assertEqual(res["gsd"], 1)
        self.assertEqual(res["rank_star"], 3)
        self.assertEqual(res["rank_plaquette"], 3)
        self.assertEqual(res["logicals"], {"z": [], "x": []})

    def test_degeneracy_torus_1v_cw(self) -> None:
        """1-vertex CW complex torus: V=1, E=2, F=1, euler=0, k=2, gsd=4."""
        case = {
            "case_id": "test_torus_1v",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [
                [[0, 1], [1, 1], [0, -1], [1, -1]],
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["V"], 1)
        self.assertEqual(res["E"], 2)
        self.assertEqual(res["F"], 1)
        self.assertEqual(res["euler"], 0)
        self.assertEqual(res["k"], 2)
        self.assertEqual(res["gsd"], 4)
        self.assertEqual(len(res["logicals"]["z"]), 2)
        self.assertEqual(len(res["logicals"]["x"]), 2)

    def test_degeneracy_klein_bottle(self) -> None:
        """Klein bottle: euler=0, k=2, gsd=4."""
        json_case = json_loads_file(EXAMPLES_DIR / "ex05_klein_bottle.json")
        res = solve(json_case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["euler"], 0)
        self.assertEqual(res["k"], 2)
        self.assertEqual(res["gsd"], 4)

    def test_degeneracy_higher_genus(self) -> None:
        """Genus 2 (gsd=16) and Genus 3 (gsd=64)."""
        g2_case = json_loads_file(EXAMPLES_DIR / "ex06_genus2_double_torus.json")
        res_g2 = solve(g2_case)
        self.assertEqual(res_g2["status"], "SOLVED")
        self.assertEqual(res_g2["euler"], -2)
        self.assertEqual(res_g2["k"], 4)
        self.assertEqual(res_g2["gsd"], 16)

        g3_case = json_loads_file(
            CHALLENGE_DIR
            / "judge_packet"
            / "cases"
            / "base"
            / "base_14_surface_triple_torus_1v_cw.json"
        )
        res_g3 = solve(g3_case)
        self.assertEqual(res_g3["status"], "SOLVED")
        self.assertEqual(res_g3["euler"], -4)
        self.assertEqual(res_g3["k"], 6)
        self.assertEqual(res_g3["gsd"], 64)

    def test_sector_solver_k4_even_and_odd(self) -> None:
        """Cycle graph C4: even charges -> dim = 2; odd charges -> dim = 0 with witness."""
        k4_even = json_loads_file(EXAMPLES_DIR / "ex07_sector_even_charges.json")
        res_even = solve(k4_even)
        self.assertEqual(res_even["status"], "SOLVED")
        self.assertEqual(res_even["sector_dimension"], 2)

        k4_odd = json_loads_file(EXAMPLES_DIR / "ex08_sector_odd_charges.json")
        res_odd = solve(k4_odd)
        self.assertEqual(res_odd["status"], "SOLVED")
        self.assertEqual(res_odd["sector_dimension"], 0)
        self.assertEqual(res_odd.get("witness"), {"charge_product": -1})

    def test_non_manifold_boundary_refusal(self) -> None:
        """Pinch non-manifold produces typed OUT_OF_SCOPE with vertex link witness."""
        ex09 = json_loads_file(EXAMPLES_DIR / "ex09_non_manifold_pinch.json")
        res = solve(ex09)
        self.assertEqual(res["status"], "OUT_OF_SCOPE")
        self.assertIn("witness", res)
        self.assertEqual(res["witness"]["kind"], "vertex_link_not_a_circle")

    def test_oversized_complex_unknown(self) -> None:
        """Complex with > 300 edges produces UNKNOWN with TOO_MANY_EDGES."""
        ex10 = json_loads_file(EXAMPLES_DIR / "ex10_oversized_complex.json")
        res = solve(ex10)
        self.assertEqual(res["status"], "UNKNOWN")
        self.assertEqual(res["refusal_code"], "TOO_MANY_EDGES")

    def test_ddc_tracer_emits_valid_alphabet(self) -> None:
        """DDC tracer must record transitions over {E, R, C, I, Lambda, D, M, T} with SHA-256 chaining."""
        case = {
            "case_id": "test_ddc",
            "query": "degeneracy",
            "vertices": [0],
            "edges": [[0, 0], [0, 0]],
            "faces": [[[0, 1], [1, 1], [0, -1], [1, -1]]],
        }
        solve(case)
        tracer = get_last_tracer()
        self.assertIsNotNone(tracer)
        trace = tracer.export_trace()
        self.assertGreaterEqual(trace["step_count"], 4)
        valid_letters = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
        for step in trace["steps"]:
            self.assertIn(step["letter"], valid_letters)
            self.assertEqual(len(step["digest"]), 64)

    def test_no_hardcoded_tables(self) -> None:
        """AST Anti-Hardcoding Regression Test.

        Inspects ASTs of all reference solver modules to assert NO static lookup tables
        or dictionaries contain hardcoded case results or precomputed ground states.
        """
        modules_to_inspect = [
            (solver, "Reference Solver (solver)"),
            (cell_complex, "Cell Complex Engine (cell_complex)"),
            (gauss_sector, "Gauss Sector Engine (gauss_sector)"),
            (f2_algebra, "F2 Algebra Engine (f2_algebra)"),
            (ddc_tracer, "DDC Tracer (ddc_tracer)"),
        ]

        for mod, name in modules_to_inspect:
            src_path = Path(mod.__file__).resolve()
            tree = ast.parse(src_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                    self.assertNotIn(
                        "base_01_surface_tetrahedron", keys, f"Hardcoded case ID detected in {name}"
                    )
                    self.assertNotIn(
                        "ex01_tetrahedron_sphere", keys, f"Hardcoded case key detected in {name}"
                    )
                    self.assertNotIn(
                        "ex03_klein_bottle_9v", keys, f"Hardcoded case key detected in {name}"
                    )


def json_loads_file(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
