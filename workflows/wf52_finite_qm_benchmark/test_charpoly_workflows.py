"""Bounded helper/plan controls using the independently derived PUBLIC fixture.

No provider invocation, runtime edits, evaluator/reference material or output
artifacts. The two actual native calls check the public fixture and one mutation.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import charpoly_workflows as workflows
import native_sidecar as sidecar
import qm_native_charpoly as qm

CHECKED = "qm_charpoly_checked_v1"
UNGATED = "qm_charpoly_ungated_v1"


class CharpolyWorkflowControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = qm.REGISTERED_SEED_SHA256
        path = Path(__file__).resolve().parent / "qm_native_charpoly_public_fixture.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != "b64692ceb7217f3e7a2de69e7259d79622d0addac5afeeabe799a312c4085d04":
            raise RuntimeError("PUBLIC_FIXTURE_CHANGED")
        fixture = json.loads(raw)
        cls.coefficients = fixture["candidate"]["coefficients"]
        cls.good_raw = sidecar.canonical({"coefficients": cls.coefficients}).decode()
        wrong = deepcopy(cls.coefficients)
        wrong[0].append({"powers": [0, 0, 0], "q": "1"})
        cls.bad_raw = sidecar.canonical({"coefficients": wrong}).decode()
        cls.good = workflows.check_candidate(cls.good_raw, cls.seed)
        cls.bad = workflows.check_candidate(cls.bad_raw, cls.seed)

    def test_01_plans_stage_ids_visibility_limits_and_pins(self):
        self.assertEqual(set(workflows.CHARPOLY_PLANS), {CHECKED, UNGATED})
        checked, ungated = (workflows.CHARPOLY_PLANS[name] for name in [CHECKED, UNGATED])
        self.assertTrue(checked["checked"])
        self.assertFalse(ungated["checked"])
        self.assertEqual([s["id"] for s in checked["stages"]], ["charpoly", "charpoly_repair", "solve"])
        self.assertEqual([s["id"] for s in ungated["stages"]], ["charpoly", "solve"])
        self.assertEqual(checked["stages"][-1], ungated["stages"][-1])
        self.assertEqual(checked["stages"][-1]["max_output_tokens"], 12000)
        self.assertEqual(checked["stages"][0]["max_output_tokens"], 2400)
        self.assertEqual(checked["stages"][1]["max_output_tokens"], 2400)
        self.assertEqual(checked["stages"][-1]["visible_artifacts"], ["charpoly_context"])
        self.assertEqual(checked["stages"][1]["visible_artifacts"], ["charpoly", "charpoly_feedback"])
        for plan in [checked, ungated]:
            self.assertIsInstance(plan["scope"], str)
            for name in ["reference_runner.py", "campaign_ledger.py", "budget_ledger.py",
                         "openrouter_provider.py", "live_campaign.py", "native_sidecar_host/Cargo.lock",
                         "native_sidecar_host/build_receipt.json", "native_sidecar_manifest.json"]:
                self.assertIn(name, plan["source_pins"])
                self.assertEqual(plan["source_pins"][name], sidecar.file_sha(workflows.HERE / name))
            self.assertTrue(any(name.endswith("pfp-native-sidecar-host.exe") for name in plan["source_pins"]))
            self.assertFalse(any("test_" in name or "fixture" in name for name in plan["source_pins"]))

    def test_02_real_preflight_and_public_context(self):
        ready = workflows.preflight(self.seed)
        self.assertEqual(ready["status"], "READY")
        self.assertEqual(ready["source_pins"], workflows.CHARPOLY_PLANS[CHECKED]["source_pins"])
        context = workflows.public_context(self.seed)
        schema = context["coefficient_contract"]
        self.assertEqual(schema["required"], ["coefficients"])
        self.assertEqual(set(schema["properties"]), {"coefficients"})
        self.assertFalse(schema["additionalProperties"])
        self.assertNotIn("accepted", context)
        self.assertNotIn("status", context)
        self.assertNotIn("coefficients", context)
        self.assertEqual(context["seed_sha256"], self.seed)

    def test_03_exact_native_check_binds_only_intermediate_assertion(self):
        self.assertTrue(self.good["accepted"])
        self.assertEqual(self.good["status"], "CERTIFIED_IDENTITY")
        receipt = self.good["verification_receipt"]
        self.assertFalse(receipt["final_answer_certified"])
        self.assertEqual(receipt["claim_scope"], "intermediate_characteristic_polynomial_identity_only")
        self.assertTrue(receipt["native_executed"])
        self.assertEqual(receipt["native_binding"]["grid_points"], 125)
        self.assertEqual(receipt["native_binding"]["native_calls"], 1)
        assertion = sidecar.assertion_text(self.coefficients)
        self.assertEqual(receipt["intermediate_assertion_sha256"], hashlib.sha256(assertion.encode()).hexdigest())
        self.assertNotEqual(receipt["intermediate_assertion_sha256"], hashlib.sha256(b"different final prose").hexdigest())
        self.assertNotIn("response", receipt)
        self.assertNotIn("coefficients", receipt)

    def test_04_mismatch_feedback_contains_only_one_bounded_witness(self):
        self.assertFalse(self.bad["accepted"])
        self.assertEqual(self.bad["status"], "REFUTED_IDENTITY")
        feedback = self.bad["feedback"]
        self.assertEqual(set(feedback), {"kind", "witness"})
        self.assertEqual(feedback["kind"], "exact_mismatch")
        self.assertEqual(set(feedback["witness"]), {"parameters", "lambda_power", "claimed", "observed", "difference"})
        self.assertEqual(feedback["witness"]["difference"], "1")
        self.assertLessEqual(len(sidecar.canonical(feedback)), workflows.MAX_FEEDBACK_BYTES)
        self.assertNotIn("coefficients", sidecar.canonical(feedback).decode())
        self.assertNotIn("matrix", sidecar.canonical(feedback).decode())

    def test_05_checked_gate_and_exactly_one_repair(self):
        self.assertEqual(workflows.next_stage(CHECKED, {})["stage"], "charpoly")
        self.assertEqual(workflows.next_stage(CHECKED, {"charpoly": self.good})["stage"], "solve")
        self.assertEqual(workflows.next_stage(CHECKED, {"charpoly": self.bad})["stage"], "charpoly_repair")
        success = workflows.next_stage(CHECKED, {"charpoly": self.bad, "charpoly_repair": self.good})
        self.assertEqual(success["stage"], "solve")
        failure = workflows.next_stage(CHECKED, {"charpoly": self.bad, "charpoly_repair": self.bad})
        self.assertIsNone(failure["stage"])
        self.assertEqual(failure["terminal_status"], "charpoly_gate_failed")
        with self.assertRaises(workflows.WorkflowError):
            workflows.next_stage(CHECKED, {"charpoly": self.bad, "charpoly_repair": self.bad, "second_repair": self.good})

    def test_06_ungated_never_repairs_and_does_not_gate_on_math(self):
        self.assertEqual(workflows.next_stage(UNGATED, {"charpoly": self.bad})["stage"], "solve")
        malformed = {"accepted": False, "status": "candidate_invalid"}
        self.assertEqual(workflows.next_stage(UNGATED, {"charpoly": malformed})["stage"], "solve")
        with self.assertRaises(workflows.WorkflowError):
            workflows.next_stage(UNGATED, {"charpoly": self.bad, "charpoly_repair": self.good})

    def test_07_identical_solver_requests_no_verdict_full_unchanged_task(self):
        task = "Synthetic whole-task transport control.\nAll sections stay here.\nDelta: Δ\n"
        for check in [self.good, self.bad]:
            artifacts = {"charpoly_context": check["solver_context"],
                         "charpoly_feedback": check["feedback"], "full_check_result": check}
            a = workflows.stage_request(CHECKED, "solve", task, self.seed, artifacts)
            b = workflows.stage_request(UNGATED, "solve", task, self.seed, artifacts)
            self.assertEqual(a, b)
            self.assertEqual(a["task"], task)
            self.assertEqual(a["max_output_tokens"], 12000)
            self.assertEqual(set(a["visible_artifacts"]), {"charpoly_context"})
            rendered = sidecar.canonical(a).decode()
            for forbidden in ["CERTIFIED_IDENTITY", "REFUTED_IDENTITY", '"accepted"', '"witness"', '"native_binding"']:
                self.assertNotIn(forbidden, rendered)

    def test_08_duplicate_nan_float_unknown_and_depth_refusals(self):
        malformed = [
            '{"coefficients":[],"coefficients":[]}',
            '{"coefficients":[NaN]}', '{"coefficients":[Infinity]}',
            '{"coefficients":[0.5]}', '```json\n{"coefficients":[]}\n```',
            '{"coefficients":[],"accepted":true}', '[' * 9 + ']' * 9,
            '"' + 'x' * workflows.MAX_RAW_BYTES + '"', '\ud800',
        ]
        with patch.object(qm, "verify", side_effect=AssertionError("malformed candidate must not reach native checker")):
            for raw in malformed:
                with self.subTest(raw=raw[:60]):
                    result = workflows.check_candidate(raw, self.seed)
                    self.assertFalse(result["accepted"])
                    self.assertEqual(result["status"], "candidate_invalid")
                    self.assertEqual(set(result["feedback"]), {"kind", "code"})
                    self.assertLessEqual(len(sidecar.canonical(result["feedback"])), workflows.MAX_FEEDBACK_BYTES)
                    context = json.loads(result["solver_context"])
                    self.assertEqual(context["representation"], "raw_candidate")
                    self.assertLessEqual(len(context["raw_text"].encode()), workflows.MAX_RAW_CONTEXT_BYTES)

    def test_09_semantic_schema_bounds_before_native(self):
        cases = []
        p = deepcopy(self.coefficients); p[0].append({"powers": [5, 0, 0], "q": "1"}); cases.append(p)
        p = deepcopy(self.coefficients); p[0][0]["powers"][0] = True; cases.append(p)
        p = deepcopy(self.coefficients); p[0][0]["q"] = "1/0"; cases.append(p)
        p = deepcopy(self.coefficients); p[-1][0]["q"] = "2"; cases.append(p)
        with patch.object(qm, "verify", side_effect=AssertionError("schema refusal before native")):
            for coefficients in cases:
                result = workflows.check_candidate(sidecar.canonical({"coefficients": coefficients}).decode(), self.seed)
                self.assertEqual(result["status"], "candidate_invalid")
                self.assertFalse(result["verification_receipt"]["native_executed"])

    def test_10_preflight_failure_halts_both_arms_without_repair(self):
        with patch.object(sidecar.NativeHost, "custody", side_effect=sidecar.Infrastructure("absent")):
            with self.assertRaises(sidecar.Infrastructure): workflows.preflight(self.seed)
            result = workflows.check_candidate(self.good_raw, self.seed)
        self.assertEqual(result["status"], "INFRASTRUCTURE_REFUSAL")
        self.assertFalse(result["accepted"])
        for plan in [CHECKED, UNGATED]:
            decision = workflows.next_stage(plan, {"charpoly": result})
            self.assertIsNone(decision["stage"])
            self.assertEqual(decision["terminal_status"], "host_infrastructure_failure")
        decision = workflows.next_stage(CHECKED, {"charpoly": self.bad, "charpoly_repair": result})
        self.assertIsNone(decision["stage"])
        self.assertEqual(decision["terminal_status"], "host_infrastructure_failure")

    def test_11_terminal_checker_infrastructure_failure_not_model_repair(self):
        with patch.object(qm, "verify", return_value={"status": "INFRASTRUCTURE_REFUSAL"}):
            result = workflows.check_candidate(self.good_raw, self.seed)
        self.assertEqual(result["status"], "INFRASTRUCTURE_REFUSAL")
        self.assertEqual(result["feedback"], {"kind": "infrastructure", "code": "host_infrastructure_failure"})
        for plan in [CHECKED, UNGATED]:
            self.assertIsNone(workflows.next_stage(plan, {"charpoly": result})["stage"])

    def test_12_registered_seed_and_source_drift_preflight(self):
        with self.assertRaises(sidecar.Infrastructure): workflows.preflight("0" * 64)
        original = sidecar.file_sha
        def changed(path):
            return "0" * 64 if Path(path).name == "Cargo.lock" else original(path)
        with patch.object(sidecar, "file_sha", side_effect=changed):
            with self.assertRaises(sidecar.Infrastructure): workflows.preflight(self.seed)

    def test_13_fresh_verified_build_capture_is_not_historical_manifest_admission(self):
        # Contract-level simulation of an independently verified rebuild. The
        # native custody owner itself is exercised for real by the other tests.
        binary, custody = sidecar.NativeHost().custody()
        rebuilt = {**custody, "build_receipt_sha256": "1" * 64}
        with patch.object(sidecar.NativeHost, "custody", return_value=(binary, rebuilt)):
            pins, captured, error = workflows._prepare_source_pins()
        self.assertIsNone(error)
        self.assertEqual(captured, rebuilt)
        self.assertEqual(pins["native_sidecar_host/build_receipt.json"], sidecar.file_sha(workflows.HERE / "native_sidecar_host/build_receipt.json"))
        with patch.object(sidecar.NativeHost, "custody", return_value=(binary, rebuilt)):
            with self.assertRaises(sidecar.Infrastructure): workflows.preflight(self.seed)

    def test_14_repair_visibility_and_receipt_injection_rejected(self):
        request = workflows.stage_request(CHECKED, "charpoly_repair", "Synthetic task", self.seed,
            {"charpoly": self.bad_raw, "charpoly_feedback": self.bad["feedback"], "full_receipt": self.bad})
        self.assertEqual(set(request["visible_artifacts"]), {"charpoly", "charpoly_feedback"})
        self.assertEqual(request["max_output_tokens"], 2400)
        with self.assertRaises(workflows.WorkflowError):
            workflows.stage_request(CHECKED, "charpoly_repair", "Synthetic task", self.seed,
                {"charpoly": self.bad_raw, "charpoly_feedback": self.bad})
        bad_context = json.loads(self.good["solver_context"])
        bad_context["accepted"] = True
        with self.assertRaises(workflows.WorkflowError):
            workflows.stage_request(UNGATED, "solve", "Synthetic task", self.seed,
                {"charpoly_context": sidecar.canonical(bad_context).decode()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
