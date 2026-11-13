"""Focused public-input transport controls; no seed text or hidden solutions."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

import qm_native_charpoly as bridge
import native_sidecar as sidecar
from test_native_sidecar import independent_determinant_polynomial, candidate_for

OBSERVATIONS = {}


def reseal(packet):
    packet["sha256"] = sidecar.digest(packet["payload"])
    return packet


def independently_act_on_computational_basis(yy_sign=1):
    """Apply Pauli bit flips/phases directly; no call to the owner's tensor code."""
    matrices = {name: [[Fraction(0)] * 4 for _ in range(4)] for name in ["J", "Delta", "K"]}
    for col in range(4):
        a, b = divmod(col, 2)
        flipped = 2 * (1 - a) + (1 - b)
        # Y|a> = i*(-1)^a |1-a>; hence Y tensor Y phase = -(-1)^(a+b).
        y_phase = -((-1) ** (a + b))
        matrices["J"][flipped][col] = Fraction(1 + yy_sign * y_phase)
        matrices["Delta"][col][col] = Fraction((-1) ** a - (-1) ** b)
        matrices["K"][col][col] = Fraction((-1) ** (a + b))
    return matrices


class RegisteredPublicBridgeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = bridge.REGISTERED_SEED_SHA256
        cls.packet = bridge.prepare_public(cls.seed)
        cls.public = cls.packet["payload"]["native_public_input"]
        # The fixture is calculated from public affine operands by independent
        # determinant/permutation expansion, never from reference/grade material.
        cls.coefficients = independent_determinant_polynomial(cls.public["matrix_coefficients"])
        cls.candidate, cls.answer = candidate_for(cls.public, cls.coefficients)

    def refused_without_native(self, packet, reason):
        with patch.object(bridge.sidecar, "verify") as native:
            receipt = bridge.verify(self.seed, self.candidate, self.answer, packet)
            native.assert_not_called()
        self.assertEqual(receipt["status"], "PUBLIC_BINDING_REFUSAL")
        self.assertEqual(receipt["reason"], reason)
        self.assertFalse(receipt["native_executed"])
        OBSERVATIONS.setdefault("binding_refusals", []).append(reason)

    def test_01_exact_pauli_transport_matches_independent_bit_action(self):
        independently = independently_act_on_computational_basis()
        payload = self.packet["payload"]
        self.assertEqual(payload["basis"], ["00", "01", "10", "11"])
        self.assertEqual(payload["seed_sha256"], self.seed)
        self.assertEqual(payload["checks"], {"pauli_compared_entries": 48,
            "exact_rational_roundtrips": 48, "constant_zero_entries": 16})
        for name in ["J", "Delta", "K"]:
            public_rows = payload["public_input_artifact"]["coefficient_matrices"][name]
            native_rows = self.public["matrix_coefficients"][name]
            for r in range(4):
                for c in range(4):
                    self.assertEqual(Fraction(public_rows[r][c]), independently[name][r][c])
                    self.assertEqual(Fraction(native_rows[r][c]), independently[name][r][c])
                    self.assertEqual(public_rows[r][c], f"{independently[name][r][c].numerator}/{independently[name][r][c].denominator}")
                    self.assertEqual(native_rows[r][c], str(independently[name][r][c]))
        self.assertEqual(self.public["matrix_coefficients"]["constant"], [["0"] * 4 for _ in range(4)])
        self.assertIn(self.seed, self.public["obligation_id"])
        OBSERVATIONS["public_transport"] = {"entries": 48, "independent_method": "computational-basis Pauli bit flips/phases",
            "public_packet_sha256": self.packet["sha256"], "native_public_input_sha256": sidecar.digest(self.public)}

    def test_02_public_contract_has_closed_coefficient_candidate_only(self):
        with patch.object(sidecar.NativeHost, "compute", side_effect=AssertionError("contract must not compute charpoly")):
            contract = bridge.public_contract(self.seed)
        schema = contract["candidate_schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(self.candidate))
        self.assertEqual(schema["properties"]["public_input_sha256"]["const"], sidecar.digest(self.public))
        self.assertEqual(schema["properties"]["obligation_id"]["const"], self.public["obligation_id"])
        self.assertNotIn("coefficient_matrices", schema["properties"])
        self.assertNotIn("native_receipt", contract)

    def test_03_registered_public_fixture_passes_exact_native_grid(self):
        receipt = bridge.verify(self.seed, self.candidate, self.answer, self.packet)
        self.assertEqual(receipt["status"], "CERTIFIED_IDENTITY")
        self.assertTrue(receipt["public_input_bound"])
        self.assertTrue(receipt["native_executed"])
        self.assertEqual(receipt["native_receipt"]["grid_points"], 125)
        self.assertEqual(receipt["native_receipt"]["native_calls"], 1)
        self.assertEqual(receipt["certified_scope"], ["characteristic_polynomial_identity"])
        for unresolved in ["spectrum projectors", "dynamics", "actual seed-byte verification (caller-owned)"]:
            self.assertIn(unresolved, receipt["unresolved"])
        OBSERVATIONS["positive_native_receipt"] = receipt

    def test_04_wrong_characteristic_coefficient_is_refuted_natively(self):
        coefficients = deepcopy(self.coefficients)
        coefficients[0].append({"powers": [0, 0, 0], "q": "1"})
        candidate, answer = candidate_for(self.public, coefficients)
        receipt = bridge.verify(self.seed, candidate, answer)
        self.assertEqual(receipt["status"], "REFUTED_IDENTITY")
        self.assertTrue(receipt["public_input_bound"])
        self.assertTrue(receipt["native_executed"])
        OBSERVATIONS["wrong_charpoly"] = {"status": receipt["status"],
            "witness": receipt["native_receipt"]["witness"], "native_calls": receipt["native_receipt"]["native_calls"]}

    def test_05_isospectral_J_sign_error_rejected_by_pauli_before_native(self):
        packet = deepcopy(self.packet)
        artifact = packet["payload"]["public_input_artifact"]
        artifact["coefficient_matrices"]["J"] = [[f"{-Fraction(x).numerator}/{Fraction(x).denominator}" for x in row]
                                                  for row in artifact["coefficient_matrices"]["J"]]
        changed = deepcopy(self.public["matrix_coefficients"])
        changed["J"] = [[str(-Fraction(x)) for x in row] for row in changed["J"]]
        self.assertEqual(independent_determinant_polynomial(changed), self.coefficients)
        self.refused_without_native(reseal(packet), "PAULI_PUBLIC_INPUT_MISMATCH")
        OBSERVATIONS["isospectral_sign_control"] = "J coefficient sign reversal leaves charpoly unchanged, but exact Pauli input replay refuses it."

    def test_06_wrong_Pauli_YY_term_is_rejected(self):
        packet = deepcopy(self.packet)
        wrong = independently_act_on_computational_basis(yy_sign=-1)
        packet["payload"]["public_input_artifact"]["coefficient_matrices"]["J"] = [
            [f"{q.numerator}/{q.denominator}" for q in row] for row in wrong["J"]]
        self.refused_without_native(reseal(packet), "PAULI_PUBLIC_INPUT_MISMATCH")

    def test_07_basis_and_convention_mismatch_refused(self):
        for key, value in [("basis", ["00", "10", "01", "11"]),
                           ("pauli_semantics", bridge.SEMANTICS.replace("Z tensor I - I tensor Z", "I tensor Z - Z tensor I"))]:
            packet = deepcopy(self.packet); packet["payload"][key] = value
            self.refused_without_native(reseal(packet), "PUBLIC_BASIS_OR_CONVENTION_MISMATCH")

    def test_08_unknown_seed_digests_are_not_admitted(self):
        for seed in ["0" * 64, "1" * 64, self.seed.upper(), None, "not-a-hash"]:
            with self.assertRaises(bridge.PublicBindingError): bridge.public_contract(seed)
            with patch.object(bridge.sidecar, "verify") as native:
                receipt = bridge.verify(seed, self.candidate, self.answer)
                native.assert_not_called()
            self.assertEqual(receipt["status"], "PUBLIC_BINDING_REFUSAL")
            self.assertEqual(receipt["reason"], "UNREGISTERED_PUBLIC_SEED")
        packet = deepcopy(self.packet); packet["payload"]["seed_sha256"] = "0" * 64
        self.refused_without_native(reseal(packet), "PUBLIC_PACKET_SEED_MISMATCH")
        packet = deepcopy(self.packet); packet["payload"]["public_input_artifact"]["seed_sha256"] = "0" * 64
        self.refused_without_native(reseal(packet), "PAULI_PUBLIC_INPUT_MISMATCH")
        OBSERVATIONS["unknown_seed_controls"] = 5

    def test_09_affine_conversion_or_constant_drift_refused(self):
        for name in ["constant", "J", "Delta", "K"]:
            packet = deepcopy(self.packet)
            packet["payload"]["native_public_input"]["matrix_coefficients"][name][0][0] = "7"
            packet["payload"]["native_public_input_sha256"] = sidecar.digest(packet["payload"]["native_public_input"])
            self.refused_without_native(reseal(packet), "PUBLIC_AFFINE_TRANSPORT_MISMATCH")

    def test_10_noncanonical_public_rational_refused(self):
        packet = deepcopy(self.packet)
        packet["payload"]["public_input_artifact"]["coefficient_matrices"]["K"][0][0] = "2/2"
        self.refused_without_native(reseal(packet), "PAULI_PUBLIC_INPUT_MISMATCH")

    def test_11_forged_provenance_checks_and_digest_refused(self):
        packet = deepcopy(self.packet); packet["payload"]["source_binding"]["pauli_source_sha256"] = "0" * 64
        self.refused_without_native(reseal(packet), "PUBLIC_PROVENANCE_MISMATCH")
        packet = deepcopy(self.packet); packet["payload"]["checks"]["pauli_compared_entries"] = 0
        self.refused_without_native(reseal(packet), "PUBLIC_PROVENANCE_MISMATCH")
        packet = deepcopy(self.packet); packet["sha256"] = "0" * 64
        self.refused_without_native(packet, "PUBLIC_PACKET_DIGEST_MISMATCH")

    def test_12_assertion_binding_and_candidate_closure_inherited(self):
        for mutate in [lambda c: c.update(assertion_text="An unrelated true statement"),
                       lambda c: c.update(coefficient_matrices={}),
                       lambda c: c.update(public_input_sha256="0" * 64)]:
            candidate = deepcopy(self.candidate); mutate(candidate)
            receipt = bridge.verify(self.seed, candidate, self.answer)
            self.assertEqual(receipt["status"], "UNSUPPORTED_OR_MALFORMED")
            self.assertFalse(receipt["native_executed"])


if __name__ == "__main__":
    start = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegisteredPublicBridgeControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    here = Path(__file__).resolve().parent
    fixture = {"schema": "pfp.qm-native-charpoly.public-fixture.v1",
               "provenance": "Derived solely from registered public Pauli matrices by independent Leibniz determinant expansion; not model-derived or a hidden/reference solution.",
               "public_packet": RegisteredPublicBridgeControls.packet,
               "candidate": RegisteredPublicBridgeControls.candidate, "answer": RegisteredPublicBridgeControls.answer}
    fixture_path = here / "qm_native_charpoly_public_fixture.json"
    fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    receipt_path = here / "qm_native_charpoly_native_receipt.json"
    positive_native_observed = "positive_native_receipt" in OBSERVATIONS
    if positive_native_observed:
        receipt_path.write_text(json.dumps(OBSERVATIONS.pop("positive_native_receipt"), indent=2) + "\n", encoding="utf-8")
    pins = {str(p.relative_to(sidecar.ROOT)): sidecar.file_sha(p) for p in
            [Path(bridge.__file__), Path(__file__), here / "hamiltonian_artifact.py", here / "native_sidecar.py",
             here / "test_native_sidecar.py", fixture_path, receipt_path] if p.exists()}
    report = {"schema": "pfp.qm-native-charpoly.validation.v1", "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "elapsed_seconds": time.monotonic() - start, "python": sys.version, "provider_calls": 0,
        "native_calls": (1 if positive_native_observed else 0) + OBSERVATIONS.get("wrong_charpoly", {}).get("native_calls", 0),
        "registered_seed_sha256": bridge.REGISTERED_SEED_SHA256, "observations": OBSERVATIONS,
        "files": pins, "limits": ["Actual public seed bytes are checked by the calling runtime, not this adapter.",
            "Only the one registered digest and its existing public Pauli interpretation are admitted.",
            "Only characteristic-polynomial identity is certified; projectors/dynamics/whole-task acceptance remain unresolved.",
            "No evaluator, hidden/reference solution, private or live-output files were accessed; existing public/checker/runtime source files were not changed."]}
    report_path = here / "qm_native_charpoly_validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "tests_run": result.testsRun, "native_calls": report["native_calls"],
                      "validation_sha256": sidecar.file_sha(report_path)}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
