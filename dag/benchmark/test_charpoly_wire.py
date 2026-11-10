"""Pure independent arithmetic/grammar controls; no files or native execution."""
from copy import deepcopy
import hashlib
from itertools import product
import json
from math import gcd
import unittest

import charpoly_wire as wire


def candidate(terms=None, leading="1"):
    return {"coefficients": [terms or [], [], [], [], [{"powers": [0, 0, 0], "q": leading}]]}


def raw(value):
    return json.dumps(value, separators=(",", ":"))


def pair(text):
    """Independent unreduced rational parser for already-valid test fixtures."""
    a, slash, b = text.partition("/")
    return int(a), int(b) if slash else 1


def evaluate_by_integer_cross_products(value, point):
    """No Fraction and no normalizer internals: unreduced numerator/denominator."""
    lam, j, delta, k = point
    total_num, total_den = 0, 1
    for power, terms in enumerate(value["coefficients"]):
        for term in terms:
            numerator, denominator = pair(term["q"])
            ej, ed, ek = term["powers"]
            numerator *= lam ** power * j ** ej * delta ** ed * k ** ek
            total_num = total_num * denominator + numerator * total_den
            total_den *= denominator
    return total_num, total_den


class CharpolyWireControls(unittest.TestCase):
    def assert_refused(self, value, code=None):
        result = wire.normalize_candidate(value)
        self.assertEqual(result["status"], "REFUSED")
        self.assertFalse(result["accepted"])
        self.assertIsNone(result["normalized_sha256"])
        self.assertIsNone(result["normalized_json"])
        self.assertIsNone(result["semantic_preservation"])
        self.assertEqual(result["transformations"], [])
        if code is not None:
            self.assertEqual(result["refusal"]["code"], code)
        return result

    def test_01_reduction_zero_sort_and_exact_sha_bindings(self):
        value = candidate([
            {"powers": [2, 0, 1], "q": "-4/1"},
            {"powers": [0, 0, 0], "q": "+6/8"},
            {"powers": [1, 2, 3], "q": "-0/7"},
        ], leading="2/2")
        original = json.dumps(value, indent=2)
        result = wire.normalize_candidate(original)
        self.assertTrue(result["accepted"])
        normalized = json.loads(result["normalized_json"])
        self.assertEqual(normalized["coefficients"][0], [
            {"powers": [0, 0, 0], "q": "3/4"}, {"powers": [2, 0, 1], "q": "-4"}])
        self.assertEqual(normalized["coefficients"][4], [{"powers": [0, 0, 0], "q": "1"}])
        self.assertEqual(result["original_sha256"], hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(result["normalized_sha256"], hashlib.sha256(result["normalized_json"].encode()).hexdigest())
        self.assertEqual({t["operation"] for t in result["transformations"]},
                         {"reduce_rational", "omit_explicit_zero", "sort_monomials", "canonical_json_serialization"})
        self.assertIn("correct characteristic polynomial", result["not_established"])

    def test_02_independent_full_polynomial_value_equivalence_on_grid(self):
        value = {"coefficients": [
            [{"powers": [4, 0, 1], "q": "-12/18"}, {"powers": [0, 2, 1], "q": "+9/3"},
             {"powers": [1, 1, 1], "q": "0/9"}],
            [{"powers": [2, 2, 2], "q": "8/12"}, {"powers": [0, 0, 0], "q": "-5/1"}],
            [{"powers": [1, 0, 4], "q": "+3"}],
            [{"powers": [4, 4, 4], "q": "+0"}],
            [{"powers": [2, 0, 0], "q": "0/3"}, {"powers": [0, 0, 0], "q": "+7/7"}],
        ]}
        result = wire.normalize_candidate(raw(value))
        self.assertTrue(result["accepted"])
        normalized = json.loads(result["normalized_json"])
        for point in product([-2, 0, 3], repeat=4):
            before_num, before_den = evaluate_by_integer_cross_products(value, point)
            after_num, after_den = evaluate_by_integer_cross_products(normalized, point)
            self.assertEqual(before_num * after_den, after_num * before_den, point)

    def test_03_bounded_rational_panel_independent_cross_multiplication(self):
        for numerator in range(-9, 10):
            for denominator in range(1, 10):
                text = f"{numerator}/{denominator}"
                value = candidate([{"powers": [2, 1, 0], "q": text}], leading="3/3")
                result = wire.normalize_candidate(raw(value))
                self.assertTrue(result["accepted"], text)
                normalized = json.loads(result["normalized_json"])
                for point in [(-2, 1, 0, 2), (1, -1, 2, -1), (0, 0, 0, 0)]:
                    a, b = evaluate_by_integer_cross_products(value, point)
                    c, d = evaluate_by_integer_cross_products(normalized, point)
                    self.assertEqual(a * d, c * b, (text, point))
                if numerator:
                    n, d = pair(normalized["coefficients"][0][0]["q"])
                    self.assertEqual(n * denominator, numerator * d)
                    self.assertEqual(gcd(abs(n), d), 1)
                    self.assertGreater(d, 0)
                else:
                    self.assertEqual(normalized["coefficients"][0], [])

    def test_04_normalization_is_idempotent(self):
        first = wire.normalize_candidate(raw(candidate([
            {"powers": [1, 0, 0], "q": "-4/1"}, {"powers": [0, 0, 0], "q": "+0/8"}], leading="9/9")))
        second = wire.normalize_candidate(first["normalized_json"])
        self.assertTrue(second["accepted"])
        self.assertEqual(first["normalized_json"], second["normalized_json"])
        self.assertEqual(second["original_sha256"], second["normalized_sha256"])
        self.assertEqual(second["transformations"], [{"operation": "canonical_json_serialization",
            "profile": "sorted-object-keys,compact,ASCII-escaped,no-floats", "changed_bytes": False}])

    def test_05_duplicate_powers_refuse_before_zero_omission(self):
        for a, b in [("0/7", "1"), ("1", "0"), ("0", "-0/3"), ("1/2", "1/2")]:
            value = candidate([{"powers": [0, 0, 0], "q": a}, {"powers": [0, 0, 0], "q": b}])
            self.assert_refused(raw(value), "DUPLICATE_POWERS")

    def test_06_rational_grammar_refuses_ambiguity_and_nonpositive_denominators(self):
        invalid = ["01", "-01", "+01", "1/01", "1/+2", "1/-2", "1/0", "0/0",
                   "1.0", "1e3", "NaN", "Infinity", " 1", "1 ", "1 /2", "--1", "1//2",
                   "1_000", "١/٢", "−1"]
        for text in invalid:
            with self.subTest(text=text):
                self.assert_refused(raw(candidate([{"powers": [0, 0, 0], "q": text}])), "RATIONAL_GRAMMAR")

    def test_07_json_numbers_bools_and_duplicate_keys_refuse(self):
        for q in [0, 1, 1.0, True, False, None]:
            self.assert_refused(raw(candidate([{"powers": [0, 0, 0], "q": q}])))
        for token in ["NaN", "Infinity", "-Infinity", "1.5"]:
            text = raw(candidate([{"powers": [0, 0, 0], "q": "PLACEHOLDER"}])).replace('"PLACEHOLDER"', token)
            self.assert_refused(text, "FLOAT_OR_NONFINITE_FORBIDDEN")
        self.assert_refused('{"coefficients":[],"coefficients":[]}', "DUPLICATE_JSON_KEY")
        text = raw(candidate([{"powers": [0, 0, 0], "q": "1"}])).replace('"q":"1"', '"q":"1","q":"2"', 1)
        self.assert_refused(text, "DUPLICATE_JSON_KEY")

    def test_08_closed_root_monomials_and_exact_exponents(self):
        value = candidate(); value["accepted"] = True
        self.assert_refused(raw(value), "CLOSED_COEFFICIENTS_OBJECT_REQUIRED")
        value = candidate([{"powers": [0, 0, 0], "q": "1", "extra": "x"}])
        self.assert_refused(raw(value), "CLOSED_MONOMIAL_OBJECT_REQUIRED")
        for powers in [[0, 0], [0, 0, 0, 0], [True, 0, 0], ["0", 0, 0], [-1, 0, 0], [5, 0, 0], [0.0, 0, 0]]:
            self.assert_refused(raw(candidate([{"powers": powers, "q": "1"}])))
        text = raw(candidate([{"powers": [0, 0, 0], "q": "1"}])).replace('"powers":[0,0,0]', '"powers":[-0,0,0]', 1)
        self.assert_refused(text, "JSON_INTEGER_OUT_OF_PROFILE")
        for count in [0, 4, 6]:
            self.assert_refused(raw({"coefficients": [[] for _ in range(count)]}), "FIVE_COEFFICIENT_ARRAYS_REQUIRED")

    def test_09_monicity_is_checked_after_exact_zero_removal(self):
        for leading in ["2", "0", "-1", "1/2"]:
            self.assert_refused(raw(candidate(leading=leading)), "NONMONIC_LEADING_COEFFICIENT")
        value = candidate()
        value["coefficients"][-1].append({"powers": [1, 0, 0], "q": "1"})
        self.assert_refused(raw(value), "NONMONIC_LEADING_COEFFICIENT")
        value = candidate(leading="4/4")
        value["coefficients"][-1].append({"powers": [1, 0, 0], "q": "-0/9"})
        self.assertTrue(wire.normalize_candidate(raw(value))["accepted"])

    def test_10_bits_term_size_depth_utf8_limits(self):
        for text in [str(2 ** 64), f"1/{2 ** 64}"]:
            self.assert_refused(raw(candidate([{"powers": [0, 0, 0], "q": text}])), "RATIONAL_COMPONENT_BIT_LIMIT")
        text = f"-{2 ** 64 - 1}/{2 ** 64 - 1}"
        self.assertTrue(wire.normalize_candidate(raw(candidate([{"powers": [0, 0, 0], "q": text}])))["accepted"])
        self.assert_refused(raw(candidate([{"powers": [0, 0, 0], "q": "1" * 43}])), "RATIONAL_CHARACTER_LIMIT")
        self.assert_refused(raw(candidate([{"powers": [0, 0, 0], "q": "0"}] * 126)), "COEFFICIENT_TERM_LIMIT")
        self.assert_refused("[" * 9 + "]" * 9, "JSON_DEPTH_LIMIT")
        self.assert_refused("x" * (wire.MAX_INPUT_BYTES + 1), "INPUT_CHARACTER_LIMIT")
        self.assert_refused('"' + "é" * 20_000 + '"', "INPUT_BYTE_LIMIT")
        self.assert_refused("\ud800", "UTF8_REQUIRED")
        self.assert_refused(b"{}", "TEXT_REQUIRED")

    def test_11_no_coefficient_invention_and_exact_transformation_witnesses(self):
        value = candidate([{"powers": [3, 2, 1], "q": "-10/20"}, {"powers": [0, 1, 0], "q": "0/5"}])
        result = wire.normalize_candidate(raw(value))
        normalized = json.loads(result["normalized_json"])
        self.assertEqual(normalized["coefficients"][0], [{"powers": [3, 2, 1], "q": "-1/2"}])
        for event in result["transformations"]:
            if event["operation"] == "reduce_rational":
                a, b = pair(event["from_q"]); c, d = pair(event["to_q"])
                self.assertEqual(a * d, c * b)
            elif event["operation"] == "omit_explicit_zero":
                self.assertEqual(pair(event["from_q"])[0], 0)

    def test_12_bad_json_and_refusal_cannot_claim_preservation(self):
        for text in ["", "{} trailing", "```json\n{}\n```", "null", "[]", "{", "\ufeff{}"]:
            result = self.assert_refused(text)
            self.assertEqual(result["original_sha256"], hashlib.sha256(text.encode()).hexdigest())
        value = candidate([{"powers": [1, 0, 0], "q": "2/4"}, {"powers": [1, 0, 0], "q": "0"}])
        self.assert_refused(raw(value), "DUPLICATE_POWERS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
