"""The legacy Python DDC API must not compute canonical functionals."""

from __future__ import annotations

from fractions import Fraction
import unittest
from unittest.mock import patch

from omega_engine_pfp.domain.ddc import (
    Cochain1,
    DDACascadeSolver,
    FunctionalBoundaryUnavailable,
    LyapunovTracker,
    SimplicialComplex,
    compute_gamma2,
    compute_phi1,
    compute_xi,
    evaluate_defect_triad,
    export_cochain_graph_data,
)


class DdcFunctionalBoundaryTests(unittest.TestCase):
    def test_python_functionals_refuse_even_for_zero_cochain(self) -> None:
        carrier = SimplicialComplex.path_graph(2)
        zero = Cochain1.zero(tuple(edge.key for edge in carrier.edges))
        for evaluate in (compute_phi1, compute_gamma2, compute_xi, evaluate_defect_triad):
            with self.subTest(evaluate=evaluate.__name__):
                with self.assertRaises(FunctionalBoundaryUnavailable) as error:
                    evaluate(carrier, zero)
                self.assertEqual(error.exception.code, "FUNCTIONAL_BOUNDARY_UNAVAILABLE")
                self.assertIn("no Rust-backed DDC adapter", str(error.exception))

    def test_python_dda_cascade_refuses_before_emitting_a_trace(self) -> None:
        carrier = SimplicialComplex.path_graph(2)
        cochain = Cochain1({("v0", "v1"): Fraction(1)})
        with patch.object(LyapunovTracker, "record_step") as record_step:
            with self.assertRaises(FunctionalBoundaryUnavailable):
                DDACascadeSolver(carrier).solve(cochain)
        record_step.assert_not_called()

    def test_graph_export_does_not_report_python_gamma2(self) -> None:
        carrier = SimplicialComplex.complete_graph(3, with_faces=True)
        cochain = Cochain1({("v0", "v1"): Fraction(1)})
        view = export_cochain_graph_data(carrier, cochain)
        self.assertIsNone(view["summary"]["closure_defect_gamma2"])
        self.assertEqual(view["summary"]["functional_status"], "FUNCTIONAL_BOUNDARY_UNAVAILABLE")
        self.assertEqual(len(view["faces"]), 1)
