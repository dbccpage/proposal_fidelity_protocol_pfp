"""Offline verification tests for EIS Two-Signal and PCIV Operational-Quotient benchmark plans.

Zero network I/O and USD 0.00 spend.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OPS = ROOT / "ops"
for _p in (ROOT, HERE, OPS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import charpoly_workflows as legacy_charpoly  # noqa: E402
import qm_host_charpoly as host_charpoly  # noqa: E402
from budget_ledger import RunLedger  # noqa: E402
from eis_pciv_workflows import (  # noqa: E402
    CHARPOLY_PROPOSE_INSTRUCTION,
    EIS_PCIV_PLANS,
    EIS_SOLVE_INSTRUCTION,
    PCIV_OBLIGATION_INSTRUCTION,
    SUPPORTED_SEED_SHA256,
    build_pciv_quotient_artifact,
    evaluate_eis_charpoly_stage,
    execute_eis_pciv_plan,
    prepare_source_pins,
    screen_normalized_charpoly_detector,
)
from openrouter_provider import OpenRouterProvider  # noqa: E402
from reference_runner import PLANS, OfflineTape, run  # noqa: E402
from summarize_runs import read_frozen_receipt  # noqa: E402

from eis.domain.thymus import ThymusGate  # noqa: E402
from eis.domain.value_objects import REGEX_MATCHER_ID, DetectorRule  # noqa: E402
from eis.use_cases.two_signal_regulation import ThymusSelfPanelBuilder  # noqa: E402


class _MockAtlasFp8Transport:
    """Offline transport snapshot modelling deepseek/deepseek-v3.2 @ atlas-cloud/fp8 metadata."""

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[bytes, dict[str, Any]]:
        if method != "GET" or path != "/models/deepseek/deepseek-v3.2/endpoints":
            raise AssertionError(f"Unexpected offline transport call: {method} {path}")
        _ = body
        payload = {
            "data": {
                "id": "deepseek/deepseek-v3.2",
                "architecture": {
                    "input_modalities": ["text"],
                    "output_modalities": ["text"],
                },
                "endpoints": [
                    {
                        "tag": "atlas-cloud/fp8",
                        "model_id": "deepseek/deepseek-v3.2",
                        "status": 0,
                        "supported_parameters": ["max_tokens"],
                        "context_length": 163840,
                        "max_completion_tokens": 16384,
                        "provider_name": "AtlasCloud",
                        "pricing": {
                            "prompt": "0.00000026",
                            "completion": "0.00000038",
                            "request": "0",
                        },
                    }
                ],
            }
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        return raw, payload


class TestEisPcivWorkflows(unittest.TestCase):
    def test_plans_structure_and_source_pins(self) -> None:
        self.assertEqual(
            set(EIS_PCIV_PLANS.keys()),
            {"eis_two_signal_charpoly_v1", "pciv_quotient_obligation_v1"},
        )
        pins = prepare_source_pins()
        self.assertIn("eis_pciv_workflows.py", pins)
        self.assertIn("qm_host_charpoly.py", pins)
        for filename, expected_sha in pins.items():
            actual_sha = hashlib.sha256((HERE / filename).read_bytes()).hexdigest()
            self.assertEqual(actual_sha, expected_sha)

        eis_spec = EIS_PCIV_PLANS["eis_two_signal_charpoly_v1"]
        self.assertEqual(eis_spec["max_paid_calls"], 2)
        self.assertEqual(len(eis_spec["stages"]), 2)
        self.assertEqual(eis_spec["stages"][0]["id"], "charpoly_propose")
        self.assertEqual(eis_spec["stages"][0]["max_output_tokens"], 1500)
        self.assertEqual(eis_spec["stages"][1]["id"], "solve")
        self.assertEqual(eis_spec["stages"][1]["max_output_tokens"], 14500)
        self.assertEqual(
            eis_spec["stages"][1]["visible_artifacts"],
            ["charpoly_propose", "eis_charpoly_context"],
        )

        pciv_spec = EIS_PCIV_PLANS["pciv_quotient_obligation_v1"]
        self.assertEqual(pciv_spec["max_paid_calls"], 1)
        self.assertEqual(len(pciv_spec["stages"]), 1)
        self.assertEqual(pciv_spec["stages"][0]["id"], "solve")
        self.assertEqual(pciv_spec["stages"][0]["max_output_tokens"], 16000)

    def test_openrouter_upper_quote_reservation_math_within_100k_cap(self) -> None:
        seed_text = (HERE / "seed_prompt.txt").read_bytes().decode("utf-8")
        transport = _MockAtlasFp8Transport()

        # Stage 1 (1,500 output tokens) -> 43,169 microUSD
        p_stage1 = OpenRouterProvider("deepseek/deepseek-v3.2", "atlas-cloud/fp8", transport)
        q1 = p_stage1.upper_quote(
            {
                "messages": [
                    {"role": "system", "content": CHARPOLY_PROPOSE_INSTRUCTION},
                    {"role": "user", "content": seed_text},
                ],
                "max_output_tokens": 1500,
                "tools": [],
                "retries": 0,
            }
        )
        self.assertEqual(q1, 43_169)

        # Stage 2 (14,500 output tokens) -> 48,109 microUSD
        p_stage2 = OpenRouterProvider("deepseek/deepseek-v3.2", "atlas-cloud/fp8", transport)
        q2 = p_stage2.upper_quote(
            {
                "messages": [
                    {"role": "system", "content": EIS_SOLVE_INSTRUCTION},
                    {"role": "user", "content": seed_text},
                ],
                "max_output_tokens": 14500,
                "tools": [],
                "retries": 0,
            }
        )
        self.assertEqual(q2, 48_109)
        self.assertEqual(q1 + q2, 91_278)
        self.assertLessEqual(q1 + q2, 100_000)

        # PCIV 1-stage matched 16,000 output tokens -> 48,679 microUSD
        p_pciv = OpenRouterProvider("deepseek/deepseek-v3.2", "atlas-cloud/fp8", transport)
        q_pciv = p_pciv.upper_quote(
            {
                "messages": [
                    {"role": "system", "content": PCIV_OBLIGATION_INSTRUCTION},
                    {"role": "user", "content": seed_text},
                ],
                "max_output_tokens": 16000,
                "tools": [],
                "retries": 0,
            }
        )
        self.assertEqual(q_pciv, 48_679)
        self.assertLessEqual(q_pciv, 100_000)

        # Verify RunLedger accepts reserving both Stage 1 and Stage 2 under the 100,000 microUSD cap
        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger = RunLedger(Path(tmp_dir) / "ledger.sqlite3")
            ledger.start("run:eis:001", SUPPORTED_SEED_SHA256, 100_000)
            ledger.reserve("run:eis:001", "call:0", "a" * 64, q1)
            ledger.reserve("run:eis:001", "call:1", "b" * 64, q2)
            summary = ledger.summary("run:eis:001")
            self.assertEqual(summary["held_microusd"], 91_278)
            self.assertFalse(summary["blocked"])
            ledger.close()

    def test_thymus_admits_normalized_matcher_while_purging_raw_regex_autoimmunity(self) -> None:
        _matcher, rule, admitted_res = screen_normalized_charpoly_detector()
        self.assertTrue(admitted_res.is_admitted)
        self.assertEqual(admitted_res.autoimmune_violations, 0)

        # Screening the identical pattern under raw regex triggers autoimmune apoptosis on self-panel
        thymus = ThymusGate(self_panel=ThymusSelfPanelBuilder.build_self_panel())
        raw_regex_rule = DetectorRule(
            rule_id="naive_raw_regex_rule",
            target_epitope="noncanonical_rational_surface",
            match_pattern=rule.match_pattern,
            matcher_id=REGEX_MATCHER_ID,
        )
        purged_res = thymus.evaluate_rule(raw_regex_rule)
        self.assertFalse(purged_res.is_admitted)
        self.assertGreater(purged_res.autoimmune_violations, 0)

    def test_eis_stage_tolerates_canonical_and_normalizes_benign_quirks(self) -> None:
        derived = host_charpoly.derive_host_charpoly(SUPPORTED_SEED_SHA256)
        canonical_json = derived["normalized_json"]

        # 1. Exact canonical wire -> TOLERATED
        exact_res = evaluate_eis_charpoly_stage(canonical_json, SUPPORTED_SEED_SHA256)
        self.assertTrue(exact_res["accepted"])
        self.assertEqual(exact_res["disposition"], "TOLERATED")
        self.assertFalse(exact_res["final_answer_certified"])
        self.assertEqual(exact_res["normalized_json"], canonical_json)

        # 2. Benign quirks: "2/2" leading coeff, explicit "+0" term, permuted monomials,
        #    uncollected equivalent terms summing to the true coefficient, and whitespace!
        quirky_coeffs = deepcopy(derived["normalized_coefficients"])
        # Reverse monomial order in lambda^0 and split first term into two equal halves
        if len(quirky_coeffs[0]) >= 2:
            quirky_coeffs[0] = list(reversed(quirky_coeffs[0]))
        first_term = quirky_coeffs[2][0]
        half_q = f"{int(first_term['q']) // 2}" if int(first_term["q"]) % 2 == 0 else f"{first_term['q']}/2"
        quirky_coeffs[2] = [
            {"powers": first_term["powers"], "q": half_q},
            {"powers": first_term["powers"], "q": half_q},
            {"powers": [1, 1, 1], "q": "+0"},
            *quirky_coeffs[2][1:],
        ]
        quirky_coeffs[4] = [{"powers": [0, 0, 0], "q": " 2/2 "}]
        quirky_text = "```json\n" + json.dumps({"coefficients": quirky_coeffs}, indent=2) + "\n```"

        # Legacy strict checker refuses this benignly formatted mathematically identical polynomial
        legacy_res = legacy_charpoly.check_candidate(quirky_text, SUPPORTED_SEED_SHA256)
        self.assertFalse(legacy_res["accepted"])

        # EIS two-signal gate normalizes value-preservingly and ADMITS Stage 2
        eis_res = evaluate_eis_charpoly_stage(quirky_text, SUPPORTED_SEED_SHA256)
        self.assertTrue(eis_res["accepted"])
        self.assertEqual(eis_res["disposition"], "DIAGNOSTIC_NORMALIZED")
        self.assertEqual(eis_res["status"], "DIAGNOSTIC_NORMALIZED")
        self.assertEqual(eis_res["normalized_json"], canonical_json)
        self.assertFalse(eis_res["final_answer_certified"])

        # Full 2-stage execution proceeds to Stage 2 synthesis on benign quirks
        tape = OfflineTape([quirky_text, "Complete 5-part synthesis derivation."])
        run_res = execute_eis_pciv_plan("eis_two_signal_charpoly_v1", tape)
        self.assertEqual(run_res["status"], "offline_fixture_completed")
        self.assertEqual(run_res["paid_calls_executed"], 2)
        self.assertEqual(run_res["answer_text"], "Complete 5-part synthesis derivation.")
        self.assertFalse(run_res["final_answer_certified"])

    def test_eis_stage_halts_on_malformed_json_and_wrong_grid_polynomial(self) -> None:
        # 1. Malformed JSON -> Host Signal 2 (MALFORMED_PAYLOAD observed by HOST) halts before Stage 2
        malformed_res = evaluate_eis_charpoly_stage('{"coefficients": [BROKEN_JSON', SUPPORTED_SEED_SHA256)
        self.assertFalse(malformed_res["accepted"])
        self.assertEqual(malformed_res["status"], "eis_two_signal_refused")
        self.assertEqual(malformed_res["danger_type"], "MALFORMED_PAYLOAD")
        self.assertEqual(malformed_res["danger_observer"], "HOST")
        self.assertFalse(malformed_res["final_answer_certified"])

        tape_malformed = OfflineTape(['{"coefficients": [BROKEN_JSON', "Should never be called"])
        halted_malformed = execute_eis_pciv_plan("eis_two_signal_charpoly_v1", tape_malformed)
        self.assertEqual(halted_malformed["status"], "eis_two_signal_refused")
        self.assertEqual(halted_malformed["paid_calls_executed"], 1)
        self.assertIsNone(halted_malformed["answer_text"])

        # 2. Syntactically valid wire for WRONG polynomial (lambda^4 alone) -> REPLAY_FAILURE on 125-point grid
        wrong_poly = '{"coefficients":[[],[],[],[],[{"powers":[0,0,0],"q":"1"}]]}'
        wrong_res = evaluate_eis_charpoly_stage(wrong_poly, SUPPORTED_SEED_SHA256)
        self.assertFalse(wrong_res["accepted"])
        self.assertEqual(wrong_res["status"], "eis_two_signal_refused")
        self.assertEqual(wrong_res["danger_type"], "REPLAY_FAILURE")
        self.assertEqual(wrong_res["danger_observer"], "HOST")
        self.assertGreater(wrong_res["grid_mismatch_count"], 0)
        self.assertFalse(wrong_res["final_answer_certified"])

        tape_wrong = OfflineTape([wrong_poly, "Should never be called"])
        halted_wrong = execute_eis_pciv_plan("eis_two_signal_charpoly_v1", tape_wrong)
        self.assertEqual(halted_wrong["status"], "eis_two_signal_refused")
        self.assertEqual(halted_wrong["paid_calls_executed"], 1)
        self.assertIsNone(halted_wrong["answer_text"])

    def test_pciv_quotient_artifact_and_exact_seed_prompt_bytes(self) -> None:
        seed_bytes = (HERE / "seed_prompt.txt").read_bytes()
        self.assertEqual(hashlib.sha256(seed_bytes).hexdigest(), SUPPORTED_SEED_SHA256)

        art = build_pciv_quotient_artifact(SUPPORTED_SEED_SHA256)
        self.assertEqual(art["schema"], "pfp.pciv-operational-quotient.v1")
        self.assertEqual(art["input_candidate_count"], 6)
        self.assertEqual(art["collapsed_duplicate_count"], 2)
        self.assertEqual(art["surviving_representative_count"], 4)
        self.assertEqual(
            set(art["collapsed_duplicate_ids"]),
            {"wf_normalize_dup_then_check", "wf_check_then_normalize_dup"},
        )
        self.assertTrue(art["noncommuting_traces_distinct"])
        self.assertEqual(art["reserve_quotas_cap10"], {"Front": 6, "Unmeasured": 3, "Baseline": 1})
        self.assertEqual(art["reserve_buckets"]["Baseline"], ["wf_direct_seed_baseline"])
        self.assertEqual(art["reserve_buckets"]["Unmeasured"], ["wf_unmeasured_wire_probe"])
        self.assertIn("wf_normalize_then_check", art["reserve_buckets"]["Front"])
        self.assertTrue(art["protected_seed_fence"]["verified_byte_identical"])
        self.assertEqual(art["protected_seed_fence"]["seed_sha256"], SUPPORTED_SEED_SHA256)
        self.assertFalse(art["limitations"]["final_answer_certified"])

        # Offline 1-stage execution preserves exact seed_prompt.txt bytes in user message
        tape = OfflineTape(["Synthetic 1-stage obligation derivation."])
        run_res = execute_eis_pciv_plan("pciv_quotient_obligation_v1", tape)
        self.assertEqual(run_res["status"], "offline_fixture_completed")
        self.assertEqual(run_res["paid_calls_executed"], 1)
        req_msgs = run_res["calls"][0]["request"]["messages"]
        self.assertEqual(req_msgs[0]["role"], "system")
        self.assertEqual(req_msgs[0]["content"], PCIV_OBLIGATION_INSTRUCTION)
        self.assertEqual(req_msgs[1]["role"], "user")
        self.assertEqual(req_msgs[1]["content"].encode("utf-8"), seed_bytes)
        self.assertFalse(run_res["final_answer_certified"])

    def test_reference_runner_end_to_end_eis_and_pciv_plans(self) -> None:
        self.assertTrue({"eis_two_signal_charpoly_v1", "pciv_quotient_obligation_v1"}.issubset(PLANS))
        seed_bytes = (HERE / "seed_prompt.txt").read_bytes()
        derived = host_charpoly.derive_host_charpoly(SUPPORTED_SEED_SHA256)
        quirky_coeffs = deepcopy(derived["normalized_coefficients"])
        quirky_coeffs[4] = [{"powers": [0, 0, 0], "q": " 2/2 "}]
        quirky_coeffs[2].append({"powers": [1, 1, 1], "q": "+0"})
        quirky_text = "```json\n" + json.dumps({"coefficients": quirky_coeffs}, indent=2) + "\n```"

        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            # 1. EIS salvages benign formatting quirks through reference_runner.run
            out_ok = base / "eis_ok"
            tape_ok = OfflineTape([quirky_text, "Offline full derivation after EIS normalization."])
            receipt_ok = run(
                "eis_two_signal_charpoly_v1",
                tape_ok,
                out_ok,
                "offline:eis:001",
                max_output_tokens=16000,
            )
            self.assertEqual(receipt_ok["status"], "offline_fixture_completed")
            self.assertEqual(len(receipt_ok["calls"]), 2)
            self.assertEqual(receipt_ok["answer_text"], "Offline full derivation after EIS normalization.")
            self.assertTrue(receipt_ok["host_checks"]["certificate_accepted"])
            self.assertFalse(receipt_ok["host_checks"]["final_answer_certified"])
            for call in receipt_ok["calls"]:
                self.assertEqual(call["request"]["messages"][1]["content"].encode("utf-8"), seed_bytes)
            frozen_ok, _ = read_frozen_receipt(out_ok / "run.json")
            self.assertEqual(frozen_ok["run_id"], "offline:eis:001")

            # 2. EIS halts before Stage 2 when Stage 1 polynomial fails 125-point grid
            out_bad = base / "eis_bad"
            wrong_poly = '{"coefficients":[[],[],[],[],[{"powers":[0,0,0],"q":"1"}]]}'
            tape_bad = OfflineTape([wrong_poly, "Unreachable Stage 2"])
            receipt_bad = run(
                "eis_two_signal_charpoly_v1",
                tape_bad,
                out_bad,
                "offline:eis:002",
                max_output_tokens=16000,
            )
            self.assertEqual(receipt_bad["status"], "eis_two_signal_refused")
            self.assertEqual(len(receipt_bad["calls"]), 1)
            self.assertIsNone(receipt_bad["answer_text"])
            self.assertFalse(receipt_bad["host_checks"]["certificate_accepted"])
            self.assertFalse(receipt_bad["host_checks"]["final_answer_certified"])
            frozen_bad, _ = read_frozen_receipt(out_bad / "run.json")
            self.assertEqual(frozen_bad["status"], "eis_two_signal_refused")

            # 3. PCIV operational quotient obligation workflow executes cleanly
            out_pciv = base / "pciv_ok"
            tape_pciv = OfflineTape(["Offline 1-stage obligation derivation."])
            receipt_pciv = run(
                "pciv_quotient_obligation_v1",
                tape_pciv,
                out_pciv,
                "offline:pciv:001",
                max_output_tokens=16000,
            )
            self.assertEqual(receipt_pciv["status"], "offline_fixture_completed")
            self.assertEqual(len(receipt_pciv["calls"]), 1)
            self.assertEqual(receipt_pciv["calls"][0]["request"]["messages"][1]["content"].encode("utf-8"), seed_bytes)
            self.assertTrue((out_pciv / "pciv_quotient_receipt.json").is_file())
            self.assertTrue(receipt_pciv["host_checks"]["quotient_verified"])
            self.assertFalse(receipt_pciv["host_checks"]["final_answer_certified"])
            frozen_pciv, _ = read_frozen_receipt(out_pciv / "run.json")
            self.assertEqual(frozen_pciv["run_id"], "offline:pciv:001")


if __name__ == "__main__":
    unittest.main()
