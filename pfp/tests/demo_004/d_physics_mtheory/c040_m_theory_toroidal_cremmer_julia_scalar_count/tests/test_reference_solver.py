"""Tests for Challenge C040 Reference Solver.

Validates algorithmic correctness, DDC 8-letter operational tracing,
strict type rejection, refusal taxonomy, and AST anti-hardcoding honesty.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.reference_solver import (
    coset_algebra,
    ddc_tracer,
    field_reduction,
    solver,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c040_m_theory_toroidal_cremmer_julia_scalar_count.reference_solver.solver import (
    get_last_tracer,
    is_exact_int,
    solve,
)


class TestReferenceSolver(unittest.TestCase):
    """Test suite for reference solver module."""

    def test_exact_int_predicate(self) -> None:
        """is_exact_int must accept genuine ints and reject bools, floats, and strings."""
        self.assertTrue(is_exact_int(7))
        self.assertTrue(is_exact_int(0))
        self.assertTrue(is_exact_int(-1))
        self.assertFalse(is_exact_int(True))
        self.assertFalse(is_exact_int(False))
        self.assertFalse(is_exact_int(7.0))
        self.assertFalse(is_exact_int("7"))
        self.assertFalse(is_exact_int(None))

    def test_all_32_queries_produce_solved(self) -> None:
        """Solver must return SOLVED for all k in 1..8 across all 4 query types."""
        expected_scalar_totals = {
            1: 1,
            2: 3,
            3: 7,
            4: 14,
            5: 25,
            6: 42,
            7: 70,
            8: 128,
        }
        expected_vector_totals = {
            1: 1,
            2: 3,
            3: 6,
            4: 10,
            5: 16,
            6: 27,
            7: 28,
            8: 0,
        }

        queries = ["scalars", "coset", "branching", "vectors"]
        for k in range(1, 9):
            for q in queries:
                case = {"id": f"test_k{k}_{q}", "k": k, "query": q}
                res = solve(case)
                self.assertEqual(res.get("status"), "SOLVED", f"Failed on k={k}, q={q}")
                self.assertEqual(res.get("k"), k)

                if q == "scalars":
                    self.assertEqual(res["scalars"]["total"], expected_scalar_totals[k])
                    # Ensure additive consistency
                    comp_sum = sum(v for k_name, v in res["scalars"].items() if k_name != "total")
                    self.assertEqual(res["scalars"]["total"], comp_sum)
                elif q == "coset":
                    self.assertEqual(res["coset"]["difference"], expected_scalar_totals[k])
                    self.assertEqual(
                        res["coset"]["dimG"] - res["coset"]["dimK"], res["coset"]["difference"]
                    )
                elif q == "branching":
                    total_rep_dim = sum(item[1] for item in res["branching"])
                    coset_info = coset_algebra.get_coset_info(k)
                    self.assertEqual(total_rep_dim, coset_info["dimG"])
                elif q == "vectors":
                    self.assertEqual(res["vectors"]["total"], expected_vector_totals[k])

    def test_refusals_on_out_of_bounds_k(self) -> None:
        """k < 1 or k > 8 must yield UNKNOWN with refusal_code K_OUT_OF_BOUNDS."""
        for invalid_k in [0, -1, -5, 9, 10, 100]:
            case = {"id": f"refuse_k_{invalid_k}", "k": invalid_k, "query": "scalars"}
            res = solve(case)
            self.assertEqual(res.get("status"), "UNKNOWN")
            self.assertEqual(res.get("refusal_code"), "K_OUT_OF_BOUNDS")

    def test_refusals_on_non_integer_k(self) -> None:
        """Float, bool, and string k values must be refused with K_OUT_OF_BOUNDS."""
        for invalid_k in [7.0, 4.5, True, False, "7", [7]]:
            case = {"id": "refuse_type_k", "k": invalid_k, "query": "scalars"}
            res = solve(case)
            self.assertEqual(res.get("status"), "UNKNOWN")
            self.assertEqual(res.get("refusal_code"), "K_OUT_OF_BOUNDS")

    def test_refusals_on_unknown_query(self) -> None:
        """Unsupported query types must yield UNKNOWN with UNKNOWN_QUERY_TYPE."""
        for bad_q in ["tensor", "fermions", "supersymmetry", ""]:
            case = {"id": "refuse_query", "k": 7, "query": bad_q}
            res = solve(case)
            self.assertEqual(res.get("status"), "UNKNOWN")
            self.assertEqual(res.get("refusal_code"), "UNKNOWN_QUERY_TYPE")

    def test_refusals_on_malformed_case(self) -> None:
        """Non-mapping case or missing mandatory fields must yield MALFORMED_CASE_STRUCTURE."""
        self.assertEqual(
            solve("not_a_dict").get("refusal_code"),
            "MALFORMED_CASE_STRUCTURE",
        )
        self.assertEqual(
            solve({"k": 7, "query": "scalars"}).get("refusal_code"),
            "MALFORMED_CASE_STRUCTURE",
        )
        self.assertEqual(
            solve({"id": "no_k", "query": "scalars"}).get("refusal_code"),
            "MALFORMED_CASE_STRUCTURE",
        )
        self.assertEqual(
            solve({"id": "no_q", "k": 7}).get("refusal_code"),
            "MALFORMED_CASE_STRUCTURE",
        )

    def test_ddc_tracer_operational_chain(self) -> None:
        """DDCTracer must record valid 8-letter steps and maintain SHA-256 hash chaining."""
        case = {"id": "trace_test_k7", "k": 7, "query": "scalars"}
        solve(case)
        tracer = get_last_tracer()
        self.assertIsNotNone(tracer)

        trace = tracer.export_trace()
        self.assertGreater(trace["step_count"], 0)
        self.assertEqual(len(trace["final_digest"]), 64)

        valid_letters = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
        for step in trace["steps"]:
            self.assertIn(step["letter"], valid_letters)
            self.assertEqual(len(step["digest"]), 64)

    def test_no_hardcoded_tables(self) -> None:
        """AST Anti-Hardcoding Regression Test.

        Inspects ASTs of all reference solver modules to assert NO static lookup tables
        map case IDs or precomputed case answer tables directly.
        """
        modules_to_inspect = [
            (solver, "solver.py"),
            (field_reduction, "field_reduction.py"),
            (coset_algebra, "coset_algebra.py"),
            (ddc_tracer, "ddc_tracer.py"),
        ]

        for mod, name in modules_to_inspect:
            src_path = Path(mod.__file__).resolve()
            tree = ast.parse(src_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                    for bad_key in [
                        "base_01_scalars_k1",
                        "base_07_scalars_k7",
                        "ex01_scalars_k7_d4",
                        "ex02_coset_k7_e7",
                        "poison_01_invite_metric_3form_only_k6",
                    ]:
                        self.assertNotIn(
                            bad_key, keys, f"Hardcoded case ID '{bad_key}' detected in {name}"
                        )


if __name__ == "__main__":
    unittest.main()
