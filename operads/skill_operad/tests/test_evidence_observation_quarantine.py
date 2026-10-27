"""Regression tests for the residual-observation claim ceiling."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from coloured_operad import ColouredOperad
from evidence_observations import (
    LegacyResidualObservation,
    RecordedResidualObservation,
    classify_residual_observation,
)
from quotient_operad import EvidenceLedger, QuotientFunctor
from residual_honesty import load_contractive_runs, load_residual_observations


class ResidualObservationQuarantineTests(unittest.TestCase):
    def test_legacy_decrease_has_zero_claim_effect(self) -> None:
        observation = classify_residual_observation(
            {
                "skill_id": "skill",
                "run_id": "run",
                "phi_before": 1.0,
                "phi_after": 0.0,
            }
        )
        self.assertIsInstance(observation, LegacyResidualObservation)
        self.assertTrue(observation.observed_decrease)
        self.assertFalse(observation.supports_contractivity)
        self.assertFalse(observation.supports_equivalence)
        self.assertFalse(observation.supports_promotion)

    def test_current_recorder_row_is_still_only_an_observation(self) -> None:
        observation = classify_residual_observation(
            {
                "schema": "core.operad.execution_trace.v1",
                "entry_id": "sha256:" + "a" * 64,
                "skill_id": "skill",
                "run_id": "run",
                "phi_before": 1.0,
                "phi_after": 0.0,
            }
        )
        self.assertIsInstance(observation, RecordedResidualObservation)
        self.assertFalse(observation.supports_contractivity)

    def test_compatibility_loader_never_returns_certified_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(
                json.dumps(
                    [{
                        "skill_id": "skill",
                        "run_id": "run",
                        "phi_before": 1.0,
                        "phi_after": 0.0,
                    }]
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_contractive_runs(path), {})
            observations = load_residual_observations(path)
            self.assertEqual(len(observations), 1)

    def test_any_number_of_scalar_rows_remains_unknown(self) -> None:
        ledger = EvidenceLedger("skill")
        for index in range(100):
            ledger.add(f"run-{index}", 1.0, 0.0)
        self.assertEqual(ledger.residual_class(), "unknown")
        self.assertFalse(ledger.is_stable(3))

        operad = ColouredOperad()
        operad.add_operation("a", "A", ["State"], "Receipt")
        operad.add_operation("b", "B", ["State"], "Receipt")
        quotient = QuotientFunctor(operad, min_instances=3)
        for operation in ("a", "b"):
            for index in range(100):
                quotient.record(operation, f"{operation}-{index}", 1.0, 0.0)
        quotient.build_meta_operad()
        self.assertFalse(quotient.congruent("a", "b"))
        self.assertEqual(quotient.cull_list(), [])


class LegacyHigherMathShellTests(unittest.TestCase):
    @staticmethod
    def _load(relative: str, name: str):
        repo = Path(__file__).resolve().parents[3]
        path = repo / relative
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    def test_hott_quasicategory_caller_values_have_no_authority(self) -> None:
        module = self._load(
            "engine/crates/homotopy_type_theory/quasi_category.py",
            "legacy_hott_quasi_category",
        )
        if module is None:
            self.skipTest("Legacy Python homotopy_type_theory migrated to Rust crate")
        self.assertTrue(module.LEGACY_DIAGNOSTIC_ONLY)
        filler = module.HornFillerResult(module.InnerHorn(2, 1), "caller")
        self.assertFalse(filler.is_unique_up_to_homotopy)
        self.assertFalse(filler.has_authoritative_verification())
        quasi = module.QuasiCategory(object(), True)
        self.assertFalse(quasi.has_authoritative_inner_kan_verification())

    def test_higher_category_booleans_have_no_authority(self) -> None:
        quasi_module = self._load(
            "engine/crates/higher_category_theory/simplicial/quasicategory.py",
            "legacy_higher_quasicategory",
        )
        if quasi_module is None:
            self.skipTest("Legacy Python higher_category_theory migrated to Rust crate")
        quasi = quasi_module.QuasiCategory("q", [1, 1], True, 2)
        self.assertTrue(quasi.claims_inner_horn_filling())
        self.assertFalse(quasi.has_authoritative_inner_horn_verification())

        horn_module = self._load(
            "engine/crates/higher_category_theory/simplicial/horn_lifting.py",
            "legacy_horn_lifting",
        )
        if horn_module is None:
            self.skipTest("Legacy Python horn_lifting migrated to Rust crate")
        horn = horn_module.HornLifting("h", 2, 1, True, "caller-ref")
        horn.validate_shell()
        self.assertFalse(horn.has_authoritative_filler_verification())


if __name__ == "__main__":
    unittest.main()
