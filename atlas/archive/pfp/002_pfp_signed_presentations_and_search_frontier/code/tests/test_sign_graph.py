"""Finite controls for signed presentation rewrites and matrix sign gauges."""

import sys
import unittest
from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_here = Path(__file__).resolve().parent
_candidates = [
    _here.parent / "genesis_alpha" / "sign_graph.py",
    _here.parents[1] / "code" / "genesis_alpha" / "sign_graph.py",
    _here.parent / "code" / "genesis_alpha" / "sign_graph.py",
]
_source = next((p for p in _candidates if p.is_file()), None)
if _source is None:
    raise FileNotFoundError("sign_graph.py not found beside test or under code/genesis_alpha")

_spec = spec_from_file_location("genesis_sign_graph_under_test", _source)
assert _spec is not None and _spec.loader is not None
_module = module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
GaugeWitness = _module.GaugeWitness
OddCycleWitness = _module.OddCycleWitness
SignedRewrite = _module.SignedRewrite
classify_matrix_sign_gauge = _module.classify_matrix_sign_gauge
classify_sign_graph = _module.classify_sign_graph
matrix_sign_graph = _module.matrix_sign_graph
verify_gauge = _module.verify_gauge
verify_odd_cycle = _module.verify_odd_cycle


class SignGraphTests(unittest.TestCase):
    def test_presentation_swap_is_gauge_exact_but_negative_quotient_loop_is_not(self) -> None:
        # An ordered two-presentation swap can be gauged at the presentation level.
        presentations = ("r0", "r1")
        swap = (SignedRewrite("r0", "r1", 1),)
        result = classify_sign_graph(presentations, swap)
        self.assertIsInstance(result, GaugeWitness)
        self.assertTrue(verify_gauge(presentations, swap, result))
        self.assertNotEqual(result.bits[0], result.bits[1])

        # A chosen B(C2)-type one-object carrier can retain an odd swap loop.
        # It is NOT the canonical quotient or action groupoid of this free swap.
        # That added loop cannot be gauged by a scalar on one node.
        quotient = ("[r0]=[r1]",)
        loop = (SignedRewrite(quotient[0], quotient[0], 1),)
        blocked = classify_sign_graph(quotient, loop)
        self.assertIsInstance(blocked, OddCycleWitness)
        self.assertTrue(verify_odd_cycle(quotient, loop, blocked))

        # The bosonic/trivial-character control has no odd holonomy.
        boson = (SignedRewrite(quotient[0], quotient[0], 0),)
        self.assertIsInstance(classify_sign_graph(quotient, boson), GaugeWitness)

    def test_odd_triangle_and_gaugeable_matrix_have_distinct_receipts(self) -> None:
        odd_triangle = ((0, 1, -1), (1, 0, -1), (-1, -1, 0))
        result = classify_matrix_sign_gauge(odd_triangle)
        vertices, edges = matrix_sign_graph(odd_triangle)
        self.assertIsInstance(result, OddCycleWitness)
        self.assertTrue(verify_odd_cycle(vertices, edges, result))
        self.assertFalse(verify_odd_cycle(vertices, edges, OddCycleWitness(((0, "0", "1"),))))

        gaugeable = ((0, Fraction(1, 2), -1), (Fraction(1, 2), 0, 2), (-1, 2, 0))
        result = classify_matrix_sign_gauge(gaugeable)
        vertices, edges = matrix_sign_graph(gaugeable)
        self.assertIsInstance(result, GaugeWitness)
        self.assertTrue(verify_gauge(vertices, edges, result))
        for i in range(3):
            for j in range(i + 1, 3):
                transformed = (-1) ** (result.bits[i] ^ result.bits[j]) * gaugeable[i][j]
                self.assertLessEqual(transformed, 0)

    def test_exact_input_and_carrier_checks(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact"):
            matrix_sign_graph(((0, 0.5), (0.5, 0)))
        with self.assertRaisesRegex(ValueError, "symmetric"):
            matrix_sign_graph(((0, 1), (-1, 0)))
        with self.assertRaisesRegex(ValueError, "outside"):
            classify_sign_graph(("a",), (SignedRewrite("a", "b", 1),))
        with self.assertRaisesRegex(ValueError, "parity"):
            classify_sign_graph(("a",), (SignedRewrite("a", "a", True),))
        with self.assertRaisesRegex(ValueError, "distinct strings"):
            classify_sign_graph((["unhashable"],), ())
        self.assertFalse(verify_odd_cycle(("a",), (SignedRewrite("a", "a", 1),), OddCycleWitness(((),))))


if __name__ == "__main__":
    unittest.main()
