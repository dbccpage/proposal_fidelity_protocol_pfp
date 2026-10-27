"""Retired entry points must return typed refusal rather than crash or admit."""

from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from operations.domain.rop.result import Err, Refusal
from operads.application.anti_skill_admission import (
    load_truth_boundary_activation,
    verify_anti_skill_admission,
    verify_verified_anti_skill_registry,
)


class TestRetiredAntiSkillBoundary(unittest.TestCase):
    def test_every_retired_entry_point_returns_explicit_refusal(self):
        arguments = dict(spec_documents=(b'{"verified":true}',), fixture_bank_document=b"not-json",
                         evaluation_receipt_documents=(), human_decision_documents=())
        results = [
            (verify_anti_skill_admission(**arguments), "governance-anti-skill-verifier"),
            (verify_verified_anti_skill_registry(registry_document=b"not-json", **arguments), "governance-anti-skill-verifier"),
            (load_truth_boundary_activation(canary_directory=Path("missing-canary"), admitted_directory=Path("missing-registry")), "governance-anti-skill-loader"),
        ]
        for result, locus in results:
            with self.subTest(locus=locus):
                self.assertIsInstance(result, Err)
                self.assertTrue(result.is_err)
                self.assertFalse(result.is_ok)
                refusal = result.unwrap_err()
                self.assertIsInstance(refusal, Refusal)
                self.assertEqual(refusal.code, "PROMPT_CIVILIZATION_RUNTIME_RETIRED")
                self.assertEqual(refusal.locus, locus)
                self.assertIn("engine/crates_rs/core_prompt_civilization", refusal.message)
                with self.assertRaises(ValueError):
                    result.unwrap()
                with self.assertRaises(FrozenInstanceError):
                    refusal.code = "APPROVED"


if __name__ == "__main__":
    unittest.main()
