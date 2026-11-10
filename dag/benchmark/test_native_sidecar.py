"""Independent public arithmetic/mutation controls; no benchmark task material."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import permutations
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

import native_sidecar as sidecar

EVIDENCE = {}


def p_add(a, b):
    result = dict(a)
    for exponent, value in b.items():
        result[exponent] = result.get(exponent, Fraction(0)) + value
    return {e: q for e, q in result.items() if q}


def p_mul(a, b):
    result = {}
    for ea, qa in a.items():
        for eb, qb in b.items():
            e = tuple(x + y for x, y in zip(ea, eb))
            result[e] = result.get(e, Fraction(0)) + qa * qb
    return {e: q for e, q in result.items() if q}


def independent_determinant_polynomial(matrices):
    """Leibniz permutation expansion, unrelated to production Faddeev recurrence."""
    n = len(matrices["constant"])
    entries = []
    for r in range(n):
        row = []
        for c in range(n):
            terms = {(0, 0, 0, 0): -Fraction(matrices["constant"][r][c])}
            if r == c:
                terms[(1, 0, 0, 0)] = Fraction(1)
            for index, name in enumerate(sidecar.PARAMETERS):
                exponent = [0, 0, 0, 0]
                exponent[index + 1] = 1
                terms[tuple(exponent)] = -Fraction(matrices[name][r][c])
            row.append({e: q for e, q in terms.items() if q})
        entries.append(row)
    answer = {}
    for permutation in permutations(range(n)):
        inversions = sum(permutation[i] > permutation[j] for i in range(n) for j in range(i + 1, n))
        term = {(0, 0, 0, 0): Fraction((-1) ** inversions)}
        for r, c in enumerate(permutation):
            term = p_mul(term, entries[r][c])
        answer = p_add(answer, term)
    return [[{"powers": list(e[1:]), "q": str(q)}
             for e, q in sorted(answer.items()) if e[0] == k] for k in range(n + 1)]


def public_for(matrices, name="public-control"):
    return {"schema": "pfp.qm-affine-charpoly-public.v1", "obligation_id": name,
            "parameters": ["J", "Delta", "K"], "matrix_coefficients": matrices}


def matrix2():
    return public_for({"constant": [["0", "0"], ["0", "0"]],
                       "J": [["1", "0"], ["0", "0"]],
                       "Delta": [["0", "1"], ["1", "0"]],
                       "K": [["0", "0"], ["0", "1"]]})


def candidate_for(public, coefficients):
    assertion = sidecar.assertion_text(coefficients)
    prefix = "Public synthetic algebra assertion.\n"
    answer = prefix + assertion
    raw = answer.encode()
    candidate = {"schema": "pfp.qm-affine-charpoly-candidate.v1",
        "public_input_sha256": sidecar.digest(public), "obligation_id": public["obligation_id"],
        "answer_sha256": hashlib.sha256(raw).hexdigest(), "assertion_span": [len(prefix.encode()), len(raw)],
        "assertion_text": assertion, "coefficients": coefficients}
    return candidate, answer


def check(public, coefficients):
    candidate, answer = candidate_for(public, coefficients)
    return sidecar.verify(public, candidate, answer)


class NativeSidecarControls(unittest.TestCase):
    def test_01_production_source_and_binary_binding(self):
        binary, receipt = sidecar.NativeHost().custody()
        self.assertTrue(binary.is_file())
        self.assertEqual(receipt["owner_sha256"], sidecar.OWNER_SHA)
        EVIDENCE["custody"] = receipt

    def test_02_native_smoke_and_independent_permutation_panel(self):
        matrices, expected = [], []
        for n in range(1, 5):
            zeros = [["0"] * n for _ in range(n)]
            for k in range(8):
                matrix = [[str(Fraction((r * 7 + c * 5 + k * 3) % 9 - 4,
                                        1 + (r + c + k) % 3)) for c in range(n)] for r in range(n)]
                affine = {"constant": matrix, **{name: zeros for name in sidecar.PARAMETERS}}
                poly = independent_determinant_polynomial(affine)
                expected.append([sum(Fraction(t["q"]) for t in terms) for terms in poly])
                matrices.append(matrix)
        actual, receipt = sidecar.NativeHost().compute(matrices)
        self.assertEqual(actual, expected)
        EVIDENCE["independent_permutation_panel"] = {"matrices": 32, "dimensions": [1, 2, 3, 4],
            "method": "Leibniz determinant polynomial over exact fractions", "native_calls": 1,
            "request_sha256": receipt["request_sha256"], "response_sha256": receipt["response_sha256"]}

    def test_03_full_three_parameter_grid_2x2(self):
        public = matrix2()
        receipt = check(public, independent_determinant_polynomial(public["matrix_coefficients"]))
        self.assertEqual(receipt["status"], "CERTIFIED_IDENTITY")
        self.assertEqual(receipt["grid_points"], 27)
        self.assertEqual(receipt["native_calls"], 1)
        self.assertEqual(receipt["grid_nodes"], [-1, 0, 1])
        self.assertIn("spectrum projectors", receipt["unresolved"])
        EVIDENCE["three_parameter_2x2"] = receipt

    def test_04_full_three_parameter_grid_4x4(self):
        affine = {name: [["0"] * 4 for _ in range(4)] for name in ["constant", *sidecar.PARAMETERS]}
        for i, name in enumerate(["J", "Delta", "K", "constant"]):
            affine[name][i][i] = "1"
        public = public_for(affine, "four-dimensional-public-control")
        receipt = check(public, independent_determinant_polynomial(affine))
        self.assertEqual(receipt["status"], "CERTIFIED_IDENTITY")
        self.assertEqual(receipt["grid_points"], 125)
        self.assertEqual(receipt["native_calls"], 1)
        self.assertEqual(len(receipt["request"]["matrices"]), 125)
        EVIDENCE["three_parameter_4x4"] = receipt

    def test_05_rational_affine_coefficients(self):
        public = matrix2()
        public["matrix_coefficients"]["constant"] = [["1/2", "1/3"], ["1/3", "-2/5"]]
        receipt = check(public, independent_determinant_polynomial(public["matrix_coefficients"]))
        self.assertEqual(receipt["status"], "CERTIFIED_IDENTITY")

    def test_05b_large_admitted_input_denominators(self):
        # One-dimensional charpoly keeps candidate coefficients within 64 bits
        # while testing the sum of four different admitted denominators.
        affine = {name: [[f"1/{den}"]] for name, den in
                  zip(["constant", *sidecar.PARAMETERS], [65521, 65519, 65497, 65479])}
        public = public_for(affine)
        receipt = check(public, independent_determinant_polynomial(affine))
        self.assertEqual(receipt["status"], "CERTIFIED_IDENTITY")
        self.assertEqual(receipt["grid_points"], 8)

    def test_06_sign_and_missing_cross_term_mutations(self):
        public = matrix2()
        coefficients = independent_determinant_polynomial(public["matrix_coefficients"])
        cases = []
        wrong_sign = deepcopy(coefficients)
        next(t for t in wrong_sign[0] if t["powers"] == [0, 2, 0])["q"] = "1"
        cases.append(wrong_sign)
        missing_cross = deepcopy(coefficients)
        missing_cross[0] = [t for t in missing_cross[0] if t["powers"] != [1, 0, 1]]
        cases.append(missing_cross)
        witnesses = []
        for mutated in cases:
            receipt = check(public, mutated)
            self.assertEqual(receipt["status"], "REFUTED_IDENTITY")
            witnesses.append(receipt["witness"])
        EVIDENCE["sign_and_cross_term_witnesses"] = witnesses

    def test_07_false_polynomial_agreeing_on_diagonal(self):
        public = matrix2()
        coefficients = independent_determinant_polynomial(public["matrix_coefficients"])
        coefficients[0].extend([{"powers": [1, 0, 0], "q": "1"},
                                {"powers": [0, 1, 0], "q": "-1"}])
        # Added J-Delta vanishes on every point of the line J=Delta=K.
        self.assertTrue(all(j - j == 0 for j in [-100, -1, 0, 1, 100]))
        receipt = check(public, coefficients)
        self.assertEqual(receipt["status"], "REFUTED_IDENTITY")
        self.assertNotEqual(receipt["witness"]["parameters"]["J"], receipt["witness"]["parameters"]["Delta"])
        EVIDENCE["insufficient_line_control"] = receipt["witness"]

    def test_08_grid_vanishing_over_degree_is_refused_before_native(self):
        public = matrix2()
        coefficients = independent_determinant_polynomial(public["matrix_coefficients"])
        # J^3-J vanishes at all three J grid nodes, but violates degree <=2.
        coefficients[0].extend([{"powers": [3, 0, 0], "q": "1"},
                                {"powers": [1, 0, 0], "q": "-1"}])
        self.assertTrue(all(j ** 3 - j == 0 for j in [-1, 0, 1]))
        receipt = check(public, coefficients)
        self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
        self.assertEqual(receipt["reason"], "PER_VARIABLE_DEGREE_LIMIT")
        self.assertFalse(receipt["native_executed"])
        EVIDENCE["over_degree_grid_control"] = {"polynomial": "J^3-J", "status": receipt["status"],
                                               "reason": receipt["reason"]}

    def test_09_bad_dimension_shape_parameters_and_denominator(self):
        original = matrix2()
        coefficients = independent_determinant_polynomial(original["matrix_coefficients"])
        cases = []
        for n in [0, 5]:
            p = deepcopy(original)
            p["matrix_coefficients"] = {name: [["0"] * n for _ in range(n)]
                                          for name in ["constant", *sidecar.PARAMETERS]}
            cases.append(p)
        p = deepcopy(original); p["matrix_coefficients"]["J"][0].append("0"); cases.append(p)
        p = deepcopy(original); del p["matrix_coefficients"]["K"]; cases.append(p)
        p = deepcopy(original); p["parameters"] = ["J"]; cases.append(p)
        for text in ["1/0", "2/4", "1/-2", "1.0", "nan", "1/2 ", str(2 ** 65)]:
            p = deepcopy(original); p["matrix_coefficients"]["J"][0][0] = text; cases.append(p)
        for p in cases:
            with self.subTest(public=p):
                receipt = check(p, coefficients)
                self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
                self.assertFalse(receipt["native_executed"])
        EVIDENCE["malformed_public_controls"] = len(cases)

    def test_10_candidate_monic_duplicates_bool_exponent_and_denominator(self):
        public = matrix2()
        original = independent_determinant_polynomial(public["matrix_coefficients"])
        cases = []
        p = deepcopy(original); p[-1][0]["q"] = "2"; cases.append(p)
        p = deepcopy(original); p[0].append(deepcopy(p[0][0])); cases.append(p)
        p = deepcopy(original); p[0][0]["powers"][0] = True; cases.append(p)
        p = deepcopy(original); p[0][0]["q"] = "1/0"; cases.append(p)
        cases.append(original[:-1])
        for p in cases:
            receipt = check(public, p)
            self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
            self.assertFalse(receipt["native_executed"])

    def test_11_binding_and_unrelated_sidecar(self):
        public = matrix2()
        coefficients = independent_determinant_polynomial(public["matrix_coefficients"])
        candidate, answer = candidate_for(public, coefficients)
        for field, replacement in [("public_input_sha256", "0" * 64),
                                   ("answer_sha256", "0" * 64), ("obligation_id", "another"),
                                   ("assertion_text", "An unrelated true statement"),
                                   ("assertion_span", [0, 3])]:
            c = deepcopy(candidate); c[field] = replacement
            receipt = sidecar.verify(public, c, answer)
            self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
            self.assertFalse(receipt["native_executed"])

    def test_12_unavailable_host_and_no_python_fallback(self):
        public = matrix2()
        candidate, answer = candidate_for(public, independent_determinant_polynomial(public["matrix_coefficients"]))
        for host in [sidecar.NativeHost(sidecar.HOST / "deliberately_absent_control"), lambda _: []]:
            receipt = sidecar.verify(public, candidate, answer, host=host)
            self.assertEqual(receipt["status"], "INFRASTRUCTURE_REFUSAL")
            self.assertFalse(receipt["native_executed"])
        EVIDENCE["unavailable_native"] = "INFRASTRUCTURE_REFUSAL; no Python fallback"

    def test_13_native_wrapper_admission(self):
        binary, _ = sidecar.NativeHost().custody()
        cases = [[], [[[]]], [[["1", "0"]]], [[["1/0"]]], [[["2/4"]]],
                 [[["1"]]] * 126]
        reasons = []
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        for matrices in cases:
            raw = sidecar.canonical({"schema": "pfp.native-sidecar.charpoly-batch.v1", "matrices": matrices})
            run = subprocess.run([str(binary)], input=raw, capture_output=True, env=env,
                                 cwd=sidecar.HOST, timeout=5)
            self.assertEqual(run.returncode, 0)
            response = sidecar.strict_json(run.stdout)
            self.assertEqual(response["status"], "REFUSED")
            reasons.append(response["reason"])
        EVIDENCE["native_admission_refusals"] = reasons

    def test_14_strict_json_and_unsupported_expression(self):
        for raw in ['{"x":1,"x":2}', '{"x":1.5}', '{"x":NaN}']:
            with self.assertRaises(sidecar.Invalid): sidecar.strict_json(raw)
        public = matrix2()
        public["matrix_coefficients"]["J"][0][0] = "1/J"
        receipt = check(public, [[], [], [{"powers": [0, 0, 0], "q": "1"}]])
        self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
        self.assertFalse(receipt["native_executed"])


if __name__ == "__main__":
    start = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeSidecarControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    controls = sidecar.HOST / "controls"
    controls.mkdir(exist_ok=True)
    pins = {}
    for name in ["three_parameter_2x2", "three_parameter_4x4"]:
        if name in EVIDENCE:
            output = controls / (name + ".json")
            output.write_text(json.dumps(EVIDENCE.pop(name), indent=2) + "\n", encoding="utf-8")
            pins[str(output.relative_to(sidecar.ROOT))] = sidecar.file_sha(output)
    report = {"schema": "pfp.native-sidecar.validation.v1", "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "elapsed_seconds": time.monotonic() - start, "python": sys.version,
        "native_executed": "independent_permutation_panel" in EVIDENCE,
        "provider_calls": 0, "evidence": EVIDENCE,
        "control_receipts": pins, "source_sha256": sidecar.file_sha(Path(sidecar.__file__)),
        "tests_sha256": sidecar.file_sha(Path(__file__)),
        "limits": ["Public synthetic controls only; no benchmark answers/evaluator accessed.",
                   "Source-extracted native exact arithmetic, not full PFP/OPERADS/EIS integration.",
                   "Projectors, eigenvectors, dynamics and public prose interpretation remain unresolved."]}
    output = sidecar.HERE / "native_sidecar_validation.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "tests_run": result.testsRun,
                      "validation_sha256": sidecar.file_sha(output)}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
