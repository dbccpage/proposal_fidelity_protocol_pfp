"""Targeted unit tests for PFP Pilot Pydantic models and YAML specifications.

Validates all 7 Pydantic-YAML duos against actual pilot output artifacts:
- trials.json -> PilotTrial, PilotTrialManifest
- observations.json -> PilotObservation, PilotObservationManifest
- records.json -> PilotRecord, PilotRecordManifest
- summary.json -> SingleModelSummary (per-model entry), CoalescedPilotSummary
- results.md -> ModelVariantPerformance, CrossModelVariantComparison, PilotResult
- tests.md -> FinishedTestSuite, PlannedTestSuite, PilotTestRegister
- Full pilot coalescence -> Pilot.load_from_directory()

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

_PILOT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "documentation"
    / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
    / "pilots"
    / "pilot_output"
)

if not (_PILOT_OUTPUT_DIR / "__init__.py").exists():
    raise unittest.SkipTest("Legacy pilot_output package has been retired (commit 65a9694).")

# Register pilot_output as a proper package in sys.modules
if "pilot_output" not in sys.modules:
    pkg = types.ModuleType("pilot_output")
    pkg.__path__ = [str(_PILOT_OUTPUT_DIR)]
    pkg.__file__ = str(_PILOT_OUTPUT_DIR / "__init__.py")
    sys.modules["pilot_output"] = pkg
    spec = importlib.util.spec_from_file_location("pilot_output", _PILOT_OUTPUT_DIR / "__init__.py")
    if spec and spec.loader:
        spec.loader.exec_module(pkg)

from pilot_output import (
    ALL_VARIANTS,
    BenchmarkTaskSpec,
    ClaimHygieneAssessment,
    CoalescedPilotSummary,
    CrossModelVariantComparison,
    ModelVariantPerformance,
    Pilot,
    PilotObservationManifest,
    PilotRecordManifest,
    PilotTrial,
    PilotTrialManifest,
    PlannedTestSuite,
    SingleModelSummary,
    TaskSegmentSpec,
)


class TestPilotModels(unittest.TestCase):
    """Verifies that all pilot models and YAML specifications are valid and strict."""

    def test_01_trials_validation(self) -> None:
        """Validates PilotTrial and PilotTrialManifest against actual trials.json."""
        trials_file = _PILOT_OUTPUT_DIR / "trials.json"
        raw_data = json.loads(trials_file.read_text(encoding="utf-8"))
        manifest = PilotTrialManifest.from_records(raw_data)
        self.assertEqual(len(manifest.trials), 16)

        first_trial = manifest.trials[0]
        self.assertEqual(first_trial.trial_id, "case0:raw")
        self.assertEqual(first_trial.variant, "raw")
        self.assertEqual(first_trial.source_id, "bench-001-primes")

        # Test immutability and digest validation
        with self.assertRaises(ValidationError):
            PilotTrial(
                trial_id="case0:raw",
                variant="raw",
                source_id="bench-001-primes",
                source_sha256=first_trial.source_sha256,
                proposal_sha256=first_trial.proposal_sha256,
                prompt_sha256="0" * 64,  # mismatched digest
                prompt=first_trial.prompt,
            )

    def test_02_observations_validation(self) -> None:
        """Validates PilotObservation and PilotObservationManifest against observations.json."""
        obs_file = _PILOT_OUTPUT_DIR / "observations.json"
        raw_data = json.loads(obs_file.read_text(encoding="utf-8"))
        manifest = PilotObservationManifest.from_records(raw_data)
        self.assertEqual(len(manifest.observations), 64)

        first_obs = manifest.observations[0]
        self.assertEqual(first_obs.trial_id, "case0:raw")
        self.assertEqual(first_obs.outcome, "pass")
        self.assertEqual(first_obs.authority_effect, "None")
        self.assertGreater(first_obs.input_tokens, 0)

    def test_03_records_validation(self) -> None:
        """Validates PilotRecord and PilotRecordManifest against records.json."""
        records_file = _PILOT_OUTPUT_DIR / "records.json"
        raw_data = json.loads(records_file.read_text(encoding="utf-8"))
        manifest = PilotRecordManifest.from_records(raw_data)
        self.assertEqual(len(manifest.records), 64)

        first_rec = manifest.records[0]
        self.assertEqual(first_rec.trial_id, "case0:raw")
        self.assertEqual(first_rec.task_id, "bench-001-primes")
        self.assertIsInstance(first_rec.cost_usd, float)
        self.assertGreaterEqual(first_rec.cost_usd, 0.0)

    def test_04_summary_validation(self) -> None:
        """Validates CoalescedPilotSummary and SingleModelSummary."""
        # 1. Coalesced summary
        coalesced_file = _PILOT_OUTPUT_DIR / "summary.json"
        raw_coalesced = json.loads(coalesced_file.read_text(encoding="utf-8"))
        summary = CoalescedPilotSummary.model_validate(raw_coalesced)

        self.assertEqual(summary.total_dispatches, 64)
        self.assertEqual(summary.total_passed, 52)
        self.assertEqual(summary.overall_pass_rate_percent, 81.25)
        self.assertEqual(len(summary.models_evaluated), 4)
        self.assertEqual(set(summary.by_variant_aggregate.keys()), set(ALL_VARIANTS))

        # 2. Per-model summary: no per-model file is retained, so build it from the
        # coalesced summary's by_model entry (same ModelVariantMetrics shape).
        raw_model = {"totals": raw_coalesced["by_model"]["openai/gpt-4o-mini"]}
        single_summary = SingleModelSummary.model_validate(raw_model)
        self.assertEqual(single_summary.authority_effect, "None")
        self.assertEqual(single_summary.totals["raw"].passed, 4)

    def test_05_result_tables_validation(self) -> None:
        """Validates ModelVariantPerformance, CrossModelVariantComparison, and PilotResult."""
        row_matrix = ModelVariantPerformance(
            model="openai/gpt-4o-mini",
            variant="raw",
            trials=4,
            passed=4,
            failed=0,
            pass_rate=100.0,
            mean_input_tok=89.2,
            mean_output_tok=22.0,
            mean_latency_ms=1233.0,
        )
        self.assertEqual(row_matrix.pass_rate, 100.0)

        row_comparison = CrossModelVariantComparison(
            variant="raw",
            total_trials=16,
            total_passed=15,
            validation_rate=93.8,
            avg_input_tokens=86.1,
            avg_output_tokens=27.9,
            avg_latency_ms=1879.0,
            overhead_vs_raw=0.0,
        )
        self.assertEqual(row_comparison.overhead_vs_raw, 0.0)

        claim_hygiene = ClaimHygieneAssessment(
            authority_effect="None",
            supports=["Current frontier models parse representations."],
            does_not_support=["No claim that representations improve raw accuracy."],
            narrowest_defensible_claim="Bounded 4-task pilot showed format compliance with token overhead.",
            next_test_needed=["Batching amortization."],
        )
        self.assertEqual(claim_hygiene.authority_effect, "None")

    def test_06_test_suites_validation(self) -> None:
        """Validates test suite models from tests.md."""
        task = BenchmarkTaskSpec(
            task_id="bench-001-primes",
            name="primes",
            expected_description="Prime extraction under 20",
            segments=[
                TaskSegmentSpec(start_byte=0, end_byte=38, role="task"),
                TaskSegmentSpec(start_byte=38, end_byte=138, role="constraint"),
            ],
        )
        self.assertEqual(task.task_id, "bench-001-primes")

        planned = PlannedTestSuite(
            test_suite_id="PFP-PILOT-002",
            title="Amortization Under Batching",
            status="PLANNED",
            objective="Measure marginal token cost under batching",
            hypothesis="Legend overhead amortizes over batching",
            target_parameters="K in {1, 5, 10, 25, 50}",
            required_gate="Receipt verifying marginal token diff",
        )
        self.assertEqual(planned.status, "PLANNED")

    def test_07_full_pilot_loader(self) -> None:
        """Validates Pilot.load_from_directory() against the actual pilot_output folder."""
        pilot = Pilot.load_from_directory(_PILOT_OUTPUT_DIR)
        self.assertEqual(pilot.pilot_id, "pfp-pilot-001")
        self.assertEqual(pilot.authority_effect, "None")
        self.assertEqual(pilot.governing_standard, "Proposal Fidelity Protocol (PFP)")
        self.assertEqual(len(pilot.trials), 16)
        self.assertEqual(len(pilot.observations), 64)
        self.assertEqual(len(pilot.records), 64)
        self.assertEqual(pilot.summary.total_dispatches, 64)
        self.assertEqual(len(pilot.result.performance_matrix), 16)
        self.assertEqual(len(pilot.result.cross_model_comparison), 4)
        self.assertEqual(len(pilot.test_register.finished_suites), 1)
        self.assertEqual(len(pilot.test_register.planned_suites), 4)

    def test_08_yaml_schemas_integrity(self) -> None:
        """Validates all 7 YAML specification files using safe_load."""
        yaml_files = [
            "trial.yaml",
            "observation.yaml",
            "record.yaml",
            "summary.yaml",
            "result.yaml",
            "test.yaml",
            "pilot.yaml",
        ]
        for yf in yaml_files:
            path = _PILOT_OUTPUT_DIR / yf
            self.assertTrue(path.exists(), f"YAML schema missing: {yf}")
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            self.assertIsInstance(data, dict, f"Failed parsing YAML: {yf}")
            self.assertIn("schema_id", data, f"Missing schema_id in {yf}")
            self.assertEqual(data.get("authority_effect"), "None", f"Missing AuthorityEffect: None in {yf}")


if __name__ == "__main__":
    unittest.main()
