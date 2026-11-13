"""Offline tests; independent Pauli basis action supplies the mathematical oracle."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import unittest
from fractions import Fraction as Q
from pathlib import Path

SOURCE = Path(__file__).with_name("hamiltonian_artifact.py")
SPEC = importlib.util.spec_from_file_location("public_hamiltonian_checker", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("checker module unavailable")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
SEED = checker.SUPPORTED_SEED_SHA256
TERMS = {"J": ((1, "X", "X"), (1, "Y", "Y")),
         "Delta": ((1, "Z", "I"), (-1, "I", "Z")), "K": ((1, "Z", "Z"),)}


def act_one(pauli, bit):
    """Return output bit and phase exponent k for i**k, without matrices."""
    if pauli == "I":
        return bit, 0
    if pauli == "X":
        return 1 - bit, 0
    if pauli == "Y":
        return 1 - bit, 1 if bit == 0 else 3
    if pauli == "Z":
        return bit, 2 * bit
    raise ValueError(pauli)


def rotate(value, exponent):
    real, imag = value
    return ((real, imag), (-imag, real), (-real, -imag), (imag, -real))[exponent % 4]


def indexed_action(vector, parameters, terms=TERMS):
    out = [(Q(0), Q(0)) for _ in range(4)]
    for coefficient, operators in terms.items():
        for sign, first, second in operators:
            for col, amplitude in enumerate(vector):
                a, phase_a = act_one(first, col // 2)
                b, phase_b = act_one(second, col % 2)
                rotated = rotate(amplitude, phase_a + phase_b)
                scale = parameters[coefficient] * sign
                row = 2 * a + b
                out[row] = tuple(out[row][k] + scale * rotated[k] for k in range(2))
    return out


def independent_candidate(terms=TERMS):
    matrices = {}
    for name in TERMS:
        columns = []
        for column in range(4):
            unit = [(Q(int(i == column)), Q(0)) for i in range(4)]
            columns.append(indexed_action(unit, {n: Q(int(n == name)) for n in TERMS}, terms))
        if any(value[1] for column in columns for value in column):
            raise AssertionError("independent result is not real")
        matrices[name] = [[f"{columns[col][row][0].numerator}/{columns[col][row][0].denominator}"
                           for col in range(4)] for row in range(4)]
    return {"schema_version": "1.0", "seed_sha256": SEED, "coefficient_matrices": matrices}


class HamiltonianArtifactTests(unittest.TestCase):
    def setUp(self):
        self.artifact = independent_candidate()

    def check(self, artifact):
        return checker.check_artifact(json.dumps(artifact), SEED)

    def test_public_seed_and_source_bindings(self):
        self.assertEqual(hashlib.sha256(SOURCE.with_name("seed_prompt.txt").read_bytes()).hexdigest(), SEED)
        result = self.check(self.artifact)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["comparison_count"], 48)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["canonical_candidate"], self.artifact)
        self.assertEqual(result["checker_source_sha256"], hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(result["seed_sha256"], SEED)
        self.assertEqual(result["basis"], ["00", "01", "10", "11"])

    def test_public_contract_contains_schema_not_an_answer(self):
        contract = checker.public_contract(SEED)
        self.assertEqual(contract["seed_sha256"], SEED)
        properties = contract["artifact_schema"]["properties"]["coefficient_matrices"]["properties"]
        self.assertEqual(set(properties), {"J", "Delta", "K"})
        self.assertTrue(all(p["type"] == "array" for p in properties.values()))
        self.assertNotIn("canonical_candidate", contract)
        self.assertNotIn("expected", json.dumps(contract))
        with self.assertRaises(ValueError):
            checker.public_contract("0" * 64)

    def test_public_input_artifact_matches_independent_derivation(self):
        host = checker.public_input_artifact(SEED)
        self.assertEqual(host, self.artifact)
        self.assertTrue(self.check(host)["accepted"])
        host["coefficient_matrices"]["J"][0][0] = "7/1"
        self.assertEqual(checker.public_input_artifact(SEED), self.artifact)
        with self.assertRaises(ValueError):
            checker.public_input_artifact("0" * 64)

    def test_random_exact_matrix_actions_against_tensor_indexed_oracle(self):
        self.assertTrue(self.check(self.artifact)["accepted"])
        rng = random.Random(14703)  # noqa: S311 - deterministic finite test, not cryptography
        for _ in range(80):
            parameters = {name: Q(rng.randint(-9, 9), rng.randint(1, 7)) for name in TERMS}
            vector = [(Q(rng.randint(-9, 9), rng.randint(1, 7)),
                       Q(rng.randint(-9, 9), rng.randint(1, 7))) for _ in range(4)]
            dense = [[sum(parameters[name] * Q(self.artifact["coefficient_matrices"][name][r][c])
                           for name in TERMS) for c in range(4)] for r in range(4)]
            observed = [tuple(sum(dense[r][c] * vector[c][part] for c in range(4))
                              for part in range(2)) for r in range(4)]
            self.assertEqual(observed, indexed_action(vector, parameters))

    def test_missing_factor_two_in_delta(self):
        matrix = self.artifact["coefficient_matrices"]["Delta"]
        for row in range(4):
            for col in range(4):
                value = Q(matrix[row][col]) / 2
                matrix[row][col] = f"{value.numerator}/{value.denominator}"
        result = self.check(self.artifact)
        self.assertFalse(result["accepted"])
        self.assertEqual({m["coefficient"] for m in result["mismatches"]}, {"Delta"})
        self.assertEqual(result["comparison_count"], 48)

    def test_wrong_yy_sign(self):
        wrong = dict(TERMS, J=((1, "X", "X"), (-1, "Y", "Y")))
        result = self.check(independent_candidate(wrong))
        self.assertFalse(result["accepted"])
        self.assertEqual({m["coefficient"] for m in result["mismatches"]}, {"J"})

    def test_wrong_basis_order(self):
        permutation = [0, 2, 1, 3]
        for name, matrix in self.artifact["coefficient_matrices"].items():
            self.artifact["coefficient_matrices"][name] = [[matrix[r][c] for c in permutation] for r in permutation]
        self.assertFalse(self.check(self.artifact)["accepted"])

    def test_zero_parameter_agreement_is_not_polynomial_certification(self):
        for name in TERMS:
            self.artifact["coefficient_matrices"][name] = [["0/1"] * 4 for _ in range(4)]
        result = self.check(self.artifact)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["errors"], [])
        self.assertIsNotNone(result["canonical_candidate"])
        self.assertEqual(result["comparison_count"], 48)
        self.assertEqual(indexed_action([(Q(1), Q(0))] * 4, dict.fromkeys(TERMS, Q(0))), [(Q(0), Q(0))] * 4)

    def test_each_single_entry_mutation_is_detected(self):
        for name in TERMS:
            for row in range(4):
                for col in range(4):
                    mutant = copy.deepcopy(self.artifact)
                    original = Q(mutant["coefficient_matrices"][name][row][col])
                    changed = original + 1
                    mutant["coefficient_matrices"][name][row][col] = f"{changed.numerator}/{changed.denominator}"
                    result = self.check(mutant)
                    self.assertEqual(result["mismatches"], [{"coefficient": name, "row": row, "col": col,
                                     "observed": f"{changed.numerator}/{changed.denominator}",
                                     "expected": f"{original.numerator}/{original.denominator}"}])
                    self.assertFalse(result["accepted"])

    def test_invalid_rational_encodings(self):
        invalid = [True, False, None, 0, 1.0, "0", "1.0", "1e0", "+1/1", "-0/1", "01/1", "1/01",
                   "1/-1", "1/0", "2/2", "0/2", " 1/1", "1/1 ", "NaN", "Infinity", "١/1", "1/1\n",
                   f"{1 << 128}/1", f"1/{1 << 128}", "9" * 1000 + "/1", [], {}]
        for value in invalid:
            with self.subTest(value=repr(value)[:60]):
                mutant = copy.deepcopy(self.artifact)
                mutant["coefficient_matrices"]["J"][0][0] = value
                result = self.check(mutant)
                self.assertFalse(result["accepted"])
                self.assertTrue(result["errors"])
                self.assertIsNone(result["canonical_candidate"])
                self.assertEqual(result["comparison_count"], 0)

    def test_component_limit_is_inclusive_and_precedes_comparison(self):
        self.artifact["coefficient_matrices"]["J"][0][0] = f"{(1 << 128) - 1}/1"
        result = self.check(self.artifact)
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["accepted"])
        self.assertEqual(result["comparison_count"], 48)

    def test_closed_shapes_and_seed(self):
        mutations = [dict(self.artifact, extra="x"), dict(self.artifact, schema_version=True),
                     dict(self.artifact, seed_sha256="0" * 64), [], None]
        for field in self.artifact:
            mutant = copy.deepcopy(self.artifact)
            del mutant[field]
            mutations.append(mutant)
        for value in ({}, {**self.artifact["coefficient_matrices"], "extra": []}, [], True):
            mutations.append(dict(self.artifact, coefficient_matrices=value))
        for matrix in ([], [["0/1"] * 4] * 3, [["0/1"] * 5] * 4, [None] * 4, True):
            mutant = copy.deepcopy(self.artifact)
            mutant["coefficient_matrices"]["J"] = matrix
            mutations.append(mutant)
        for mutant in mutations:
            result = self.check(mutant)
            self.assertTrue(result["errors"])
            self.assertFalse(result["accepted"])
        for seed in (None, True, "", "0" * 64, SEED.upper()):
            self.assertFalse(checker.check_artifact(json.dumps(self.artifact), seed)["accepted"])

    def test_duplicate_keys_and_malformed_json(self):
        valid = json.dumps(self.artifact)
        duplicate_root = valid.replace('"schema_version": "1.0"', '"schema_version": "1.0", "schema_version": "1.0"')
        duplicate_nested = valid.replace('"coefficient_matrices": {', '"coefficient_matrices": {"J": [],')
        escaped_duplicate = valid.replace(
            '"schema_version": "1.0"', '"schema_version": "1.0", "schema_versio\\u006e": "1.0"'
        )
        for text in (duplicate_root, duplicate_nested, escaped_duplicate, "", "```json\n" + valid + "\n```",
                     valid + valid, valid[:-1], "[" * 100 + "]" * 100, valid.replace('"0/1"', 'NaN', 1),
                     valid.replace('"0/1"', 'Infinity', 1), valid.replace('"0/1"', '-Infinity', 1),
                     valid.replace('"0/1"', '1e10000', 1), "\ud800", b"{}"):
            result = checker.check_artifact(text, SEED)
            self.assertFalse(result["accepted"])
            self.assertTrue(result["errors"])
            self.assertIsNone(result["canonical_candidate"])

    def test_exact_utf8_byte_limit(self):
        valid = json.dumps(self.artifact)
        padded = valid + " " * (checker.MAX_INPUT_BYTES - len(valid.encode("utf8")))
        self.assertTrue(checker.check_artifact(padded, SEED)["accepted"])
        self.assertFalse(checker.check_artifact(padded + " ", SEED)["accepted"])
        self.assertIn("byte limit", checker.check_artifact("é" * 17000, SEED)["errors"][0])


if __name__ == "__main__":
    unittest.main()
