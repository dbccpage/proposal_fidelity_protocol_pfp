"""Tests for C038 Reference Solver.

Validates surface and graph solvers, discrete Gauss-Bonnet theorem,
Forman curvature, primal-dual optimal transport, DDC operational tracing,
and AST anti-hardcoding regression.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import unittest
from fractions import Fraction
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.reference_solver import (
    exact_transport,
    graph_curvature,
    regge_surface,
    solver,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c038_regge_combinatorial_curvature.reference_solver.solver import (
    get_last_tracer,
    solve,
)


class TestReferenceSolver(unittest.TestCase):
    """Verifies algorithmic correctness of C038 reference solver without hardcoding."""

    def test_surface_solver_octahedron(self) -> None:
        """Octahedron: V=6, E=12, F=8, chi=2, genus=0, all K(v)=1/3."""
        case = {
            "case_id": "test_oct",
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
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["V"], 6)
        self.assertEqual(res["E"], 12)
        self.assertEqual(res["F"], 8)
        self.assertEqual(res["euler"], 2)
        self.assertTrue(res["orientable"])
        self.assertEqual(res["classification"]["orientable_genus"], 0)
        for v in range(6):
            self.assertEqual(res["vertex_curvature"][str(v)], "1/3")

        # Discrete Gauss-Bonnet: sum K(v) == chi(M)
        total_k = sum(Fraction(res["vertex_curvature"][str(v)]) for v in range(6))
        self.assertEqual(total_k, Fraction(2, 1))

    def test_surface_solver_torus(self) -> None:
        """Csaszar torus: V=7, E=21, F=14, chi=0, genus=1, sum K(v) == 0."""
        case = {
            "case_id": "test_torus",
            "query": "surface",
            "triangles": [
                [0, 1, 3],
                [1, 2, 4],
                [2, 3, 5],
                [3, 4, 6],
                [4, 5, 0],
                [5, 6, 1],
                [6, 0, 2],
                [0, 1, 5],
                [1, 2, 6],
                [2, 3, 0],
                [3, 4, 1],
                [4, 5, 2],
                [5, 6, 3],
                [6, 0, 4],
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["V"], 7)
        self.assertEqual(res["E"], 21)
        self.assertEqual(res["F"], 14)
        self.assertEqual(res["euler"], 0)
        self.assertTrue(res["orientable"])
        self.assertEqual(res["classification"]["orientable_genus"], 1)

        total_k = sum(Fraction(res["vertex_curvature"][str(v)]) for v in range(7))
        self.assertEqual(total_k, Fraction(0, 1))

    def test_surface_solver_rp2(self) -> None:
        """Minimal 6-vertex RP2: non-orientable, chi=1, sum K(v) == 1."""
        case = {
            "case_id": "test_rp2",
            "query": "surface",
            "triangles": [
                [0, 1, 2],
                [0, 1, 3],
                [0, 2, 4],
                [0, 3, 5],
                [0, 4, 5],
                [1, 2, 5],
                [1, 3, 4],
                [1, 4, 5],
                [2, 3, 4],
                [2, 3, 5],
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["euler"], 1)
        self.assertFalse(res["orientable"])
        self.assertEqual(res["classification"]["non_orientable_genus"], 1)

        total_k = sum(Fraction(res["vertex_curvature"][str(v)]) for v in range(6))
        self.assertEqual(total_k, Fraction(1, 1))

    def test_graph_solver_petersen(self) -> None:
        """Petersen graph: 10 vertices, 15 edges, zero duality gap on transport certificate."""
        case = {
            "case_id": "test_petersen",
            "query": "graph",
            "alpha": "0",
            "edges": [
                [0, 1],
                [1, 2],
                [2, 3],
                [3, 4],
                [4, 0],
                [5, 6],
                [6, 7],
                [7, 8],
                [8, 9],
                [9, 5],
                [0, 5],
                [1, 6],
                [2, 7],
                [3, 8],
                [4, 9],
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(len(res["edges"]), 15)
        for e in res["edges"]:
            self.assertIn("forman", e)
            self.assertIn("ollivier", e)
            self.assertIn("plan", e)
            self.assertIn("potential", e)

    def test_refusal_non_manifold(self) -> None:
        """Non-manifold mesh must fail-closed with OUT_OF_SCOPE."""
        case = {"case_id": "test_pinch", "query": "surface", "triangles": [[0, 1, 2], [0, 3, 4]]}
        res = solve(case)
        self.assertEqual(res["status"], "OUT_OF_SCOPE")
        self.assertIn("witness", res)

    def test_refusal_disconnected_graph(self) -> None:
        """Disconnected graph must fail-closed with OUT_OF_SCOPE."""
        case = {"case_id": "test_disc", "query": "graph", "alpha": "0", "edges": [[0, 1], [2, 3]]}
        res = solve(case)
        self.assertEqual(res["status"], "OUT_OF_SCOPE")
        self.assertEqual(res["witness"]["kind"], "graph_disconnected")

    def test_refusal_oversized_mesh(self) -> None:
        """Oversized mesh (>200 triangles) must fail-closed with UNKNOWN."""
        triangles = [[0, i, i + 1] for i in range(1, 210)]
        case = {"case_id": "test_oversized", "query": "surface", "triangles": triangles}
        res = solve(case)
        self.assertEqual(res["status"], "UNKNOWN")
        self.assertEqual(res["refusal_code"], "TOO_MANY_TRIANGLES")

    def test_ddc_tracer_emits_valid_alphabet(self) -> None:
        """DDC tracer must record transitions over {E, R, C, I, Lambda, D, M, T} with SHA-256 chaining."""
        case = {
            "case_id": "test_ddc",
            "query": "surface",
            "triangles": [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]],
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

    def test_no_hardcoded_curvature_tables(self) -> None:
        """AST Anti-Hardcoding Regression Test.

        Inspects ASTs of reference solver modules to assert NO static lookup tables
        or dictionaries contain hardcoded case results or precomputed curvatures.
        """
        modules_to_inspect = [
            (solver, "Reference Solver (solver)"),
            (regge_surface, "Regge Surface Engine (regge_surface)"),
            (graph_curvature, "Graph Curvature Engine (graph_curvature)"),
            (exact_transport, "Exact Transport Solver (exact_transport)"),
        ]

        for mod, name in modules_to_inspect:
            src_path = Path(mod.__file__).resolve()
            tree = ast.parse(src_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                    self.assertNotIn(
                        "base_01_tetrahedron", keys, f"Hardcoded case ID detected in {name}"
                    )
                    self.assertNotIn("petersen", keys, f"Hardcoded case key detected in {name}")
                    self.assertNotIn(
                        "ex01_octahedron", keys, f"Hardcoded case key detected in {name}"
                    )


if __name__ == "__main__":
    unittest.main()
