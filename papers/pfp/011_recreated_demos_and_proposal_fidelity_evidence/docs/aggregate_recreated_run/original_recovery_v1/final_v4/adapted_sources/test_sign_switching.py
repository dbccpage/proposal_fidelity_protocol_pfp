"""Finite exact certificates for the Demo 2 diagonal-sign subproblem."""
from decimal import Decimal
from fractions import Fraction
from itertools import product
from pathlib import Path
import sys
import unittest
from paper011_recovered_demo2.sign_switching import classify_sign_gauge, parse_matrix, verify_cycle, verify_gauge

class SignSwitchingTests(unittest.TestCase):

    def test_four_state_transverse_field_ising_identity_gauge(self) -> None:
        h = [[-1, -1, -1, 0], [-1, 1, 0, -1], [-1, 0, 1, -1], [0, -1, -1, -1]]
        result = classify_sign_gauge(h)
        self.assertEqual(result.gauge, (0, 0, 0, 0))
        self.assertEqual(result.transformed, result.matrix)
        self.assertIsNone(result.cycle)
        self.assertTrue(verify_gauge(h, result.gauge))

    def test_nonstoquastic_input_with_exact_sign_gauge(self) -> None:
        h = [[0, 1, -1], [1, 0, 1], [-1, 1, 0]]
        result = classify_sign_gauge(h)
        self.assertEqual(result.gauge, (0, 1, 0))
        self.assertTrue(verify_gauge(h, result.gauge))
        self.assertEqual(result.transformed[0][1], -1)
        self.assertEqual(result.transformed[1][2], -1)
        self.assertEqual(result.transformed[0][2], -1)
        self.assertFalse(verify_gauge(h, (0, 0, 0)))

    def test_odd_cycle_is_checkable_no_gauge_certificate(self) -> None:
        h = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
        result = classify_sign_gauge(h)
        self.assertIsNone(result.gauge)
        self.assertIsNone(result.transformed)
        self.assertTrue(verify_cycle(h, result.cycle))
        self.assertEqual(result.cycle[0], result.cycle[-1])
        self.assertFalse(any((verify_gauge(h, bits) for bits in product((0, 1), repeat=3))))

    def test_zero_edges_do_not_impose_constraints(self) -> None:
        h = [[Fraction(1, 2), Fraction(2, 3), 0, 0], [Fraction(2, 3), 0, 0, 0], [0, 0, -2, 0], [0, 0, 0, Decimal('0.125')]]
        result = classify_sign_gauge(h)
        self.assertEqual(result.gauge, (0, 1, 0, 0))
        self.assertEqual(result.transformed[0][1], Fraction(-2, 3))
        self.assertEqual(result.transformed[0][0], Fraction(1, 2))
        self.assertEqual(result.transformed[3][3], Fraction(1, 8))
        self.assertTrue(verify_gauge(h, result.gauge))

    def test_rational_string_transport_is_lossless(self) -> None:
        self.assertEqual(parse_matrix([['1/3', '-0.125'], ['-1/8', '2']]), ((Fraction(1, 3), Fraction(-1, 8)), (Fraction(-1, 8), Fraction(2))))

    def test_malformed_matrix_and_invalid_witnesses_fail_closed(self) -> None:
        bad_matrices = [[], [[0, 1], [1]], [[0, 1], [2, 0]], [[0, True], [True, 0]], [[0, 1.0], [1.0, 0]], [[0, float('nan')], [float('nan'), 0]], [[0, Decimal('NaN')], [Decimal('NaN'), 0]], [[0, Decimal('Infinity')], [Decimal('Infinity'), 0]], [[0, 'nan'], ['nan', 0]], [[0, 1j], [1j, 0]]]
        for h in bad_matrices:
            with self.subTest(h=repr(h)):
                with self.assertRaises(ValueError):
                    parse_matrix(h)
        h = [[0, -1], [-1, 0]]
        self.assertFalse(verify_gauge(h, (True, 0)))
        self.assertFalse(verify_gauge(h, (0,)))
        self.assertFalse(verify_gauge(h, (0, 2)))
        self.assertFalse(verify_cycle(h, (0, 1, 0)))

    def test_four_vertex_signed_graphs_match_exhaustive_search(self) -> None:
        edges = [(i, j) for i in range(4) for j in range(i + 1, 4)]
        for signs in product((-1, 0, 1), repeat=len(edges)):
            h = [[0] * 4 for _ in range(4)]
            for (i, j), sign in zip(edges, signs):
                h[i][j] = h[j][i] = sign
            result = classify_sign_gauge(h)
            exists = any((verify_gauge(h, bits) for bits in product((0, 1), repeat=4)))
            self.assertEqual(result.gaugeable, exists, msg=f'edge signs: {signs}')
            if exists:
                self.assertTrue(verify_gauge(h, result.gauge))
            else:
                self.assertTrue(verify_cycle(h, result.cycle))
