"""Focused regression tests for the Paper 001 boundary repairs."""

import copy
import json
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import native_functional as nf  # noqa: E402
import symbol_game_governor as sg  # noqa: E402


class NativeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.request = {"vertices": ["a", "b", "c"], "edges": [
            {"u": "a", "v": "b", "weight": "2", "claim": "1"},
            {"u": "b", "v": "c", "weight": "2", "claim": "1"},
            {"u": "c", "v": "a", "weight": "2", "claim": "1"},
        ]}
        self.good = {"status": "PASS", "result": {
            "phi1": "6", "gauge": {"a": "0", "b": "-2", "c": "-1"},
            "forests_checked": 3,
        }}

    def call(self, body, returncode=0):
        completed = subprocess.CompletedProcess(["mock"], returncode, json.dumps(body), "")
        with patch.object(nf.subprocess, "run", return_value=completed):
            return nf._run_native(Path("mock"), self.request)

    def test_valid_exact_response(self):
        value, gauge = self.call(self.good)
        self.assertEqual(value, Fraction(6))
        self.assertEqual(gauge, {"a": 0, "b": -2, "c": -1})

    def test_malformed_shapes_raise_typed_error(self):
        for body in [[], None, 7, "PASS", {"status": "PASS", "result": []},
                     {"status": "PASS", "result": {"phi1": "6", "gauge": [], "forests_checked": 3}}]:
            with self.subTest(body=body), self.assertRaises(nf.NativeFunctionalProtocolError):
                self.call(body)

    def test_bad_rational_values_raise_typed_error(self):
        for value in [6.0, True, False, "6.0", "1e0", "1/0"]:
            for field in ["phi1", "gauge"]:
                body = copy.deepcopy(self.good)
                if field == "phi1":
                    body["result"][field] = value
                else:
                    body["result"][field]["a"] = value
                with self.subTest(value=value, field=field), self.assertRaises(nf.NativeFunctionalProtocolError):
                    self.call(body)

    def test_incomplete_or_inconsistent_result_rejected(self):
        variants = []
        for change in [{"phi1": "-1"}, {"phi1": "2"}, {"gauge": {"a": "0"}},
                       {"forests_checked": True}, {"forests_checked": 0},
                       {"forests_checked": 100001}]:
            body = copy.deepcopy(self.good)
            body["result"].update(change)
            variants.append(body)
        missing = copy.deepcopy(self.good)
        del missing["result"]["forests_checked"]
        variants.append(missing)
        for body in variants:
            with self.subTest(body=body), self.assertRaises(nf.NativeFunctionalProtocolError):
                self.call(body)

    def test_refusal_timeout_and_nonzero_exit_keep_typed_errors(self):
        with self.assertRaises(nf.NativeFunctionalRefusal):
            self.call({"status": "REFUSE", "reason": "EnumerationLimit"}, 2)
        with self.assertRaises(nf.NativeFunctionalProtocolError):
            self.call(self.good, 2)
        with patch.object(nf.subprocess, "run", side_effect=subprocess.TimeoutExpired("mock", 30)):
            with self.assertRaises(nf.NativeFunctionalTimeout):
                nf._run_native(Path("mock"), self.request)

    def test_native_refusal_does_not_call_reference_fallback(self):
        with patch.object(nf, "_find_binary", return_value=Path("mock")), \
             patch.object(nf, "_run_native", side_effect=nf.NativeFunctionalRefusal("EnumerationLimit")), \
             patch.object(sg, "compute_exact_phi_1") as fallback:
            with self.assertRaises(nf.NativeFunctionalRefusal):
                nf.compute_graph_phi1(["a", "b"], [("a", "b", 1)], {("a", "b"): 1})
            fallback.assert_not_called()


class GovernorBoundaryTests(unittest.TestCase):
    def edge_governor(self):
        return sg.SymbolGameGovernor(sg.ConstraintGraph(("u", "v"), (sg.Edge("u", "v", 1),)),
                                     {("u", "v"): 1})

    def test_float_boolean_and_decimal_proposals_refused_without_state_change(self):
        for value in [0.1, True, False, "0.1", "1e-1"]:
            for move in ["CUT", "ASSERT"]:
                governor = self.edge_governor()
                original = (dict(governor.section), dict(governor.claims))
                payload = ({"potentials": {"v": value}} if move == "CUT" else
                           {"u": "u", "v": "v", "value": value})
                outcome = governor.execute_move(move, payload)
                with self.subTest(value=value, move=move):
                    self.assertFalse(outcome.admitted)
                    self.assertEqual((dict(governor.section), dict(governor.claims)), original)

    def test_exact_fraction_string_proposal_remains_admissible(self):
        governor = self.edge_governor()
        outcome = governor.execute_move("CUT", {"potentials": {"v": "1/2"}})
        self.assertTrue(outcome.admitted)
        self.assertEqual(outcome.defect, Fraction(1, 2))

    def test_positive_optimum_is_hold_and_zero_cost_is_exact(self):
        graph = sg.ConstraintGraph(("a", "b", "c"),
            (sg.Edge("a", "b", 1), sg.Edge("b", "c", 2), sg.Edge("c", "a", 3)))
        governor = sg.SymbolGameGovernor(graph, {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1})
        outcome = governor.execute_move("CUT", {"potentials": {"b": -2, "c": -1}})
        self.assertEqual(outcome.phi_1, 3)
        self.assertEqual(outcome.verdict, sg.StepVerdict.HOLD)
        self.assertEqual(governor.execute_move("VERIFY", {}).verdict, sg.StepVerdict.HOLD)
        exact = self.edge_governor().execute_move("CUT", {"potentials": {"v": 1}})
        self.assertEqual(exact.verdict, sg.StepVerdict.EXACT)


if __name__ == "__main__":
    unittest.main()
