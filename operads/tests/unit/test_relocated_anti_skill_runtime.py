"""The relocated anti-skill runtime must reproduce the retired one's recorded evidence.

The runtime moved here from the retired `engine/crates/prompt_civilization`
(39c9deb75). The autop_001 canary run pinned three specs, their fixture bank and
three evaluation receipts, all produced by the retired source. Those bytes are
the oracle: identifiers come from `canonical_id` and every document must
re-serialize to exactly what was recorded.

AuthorityEffect: None.
"""

import unittest
from pathlib import Path

from operads.application.anti_skill import anti_skill_v2 as runtime
from operads.domain.anti_skills.anti_skill_v2 import (
    canonical_json_bytes,
)

CANARY = (
    Path(__file__).resolve().parents[3]
    / "operations" / "evidence" / "core_campaign" / "autop_001" / "canary"
)
# Source digest of the retired prompt_civilization anti_skill_v2 modules; the
# pinned specs bind it.
RETIRED_IMPLEMENTATION_DIGEST = (
    "sha256:bafe4de533f96026200eafa183d6a6cada2d87081be3d0aa0faa2a911e47568a"
)


def _specs():
    return tuple(
        runtime.parse_antiskill_spec_v2(path.read_bytes()).unwrap()
        for path in sorted(CANARY.glob("*.spec.json"))
    )


def _bank():
    raw = (CANARY / "truth-boundary.fixture-bank.json").read_bytes()
    return runtime.parse_antiskill_fixture_bank_v1(raw).unwrap()


class TestRelocatedAntiSkillRuntime(unittest.TestCase):
    def test_pinned_canary_documents_parse_to_their_exact_bytes(self):
        parsers = (
            ("*.spec.json", runtime.parse_antiskill_spec_v2),
            ("*.evaluation-receipt.json", runtime.parse_antiskill_evaluation_receipt_v2),
            ("*.fixture-bank.json", runtime.parse_antiskill_fixture_bank_v1),
        )
        seen = 0
        for pattern, parse in parsers:
            for path in sorted(CANARY.glob(pattern)):
                with self.subTest(document=path.name):
                    parsed = parse(path.read_bytes())
                    self.assertTrue(parsed.is_ok, parsed)
                    self.assertEqual(
                        canonical_json_bytes(parsed.unwrap().to_dict()), path.read_bytes()
                    )
                    seen += 1
        self.assertEqual(seen, 7)

    def test_detector_reproduces_the_recorded_receipts_byte_for_byte(self):
        current = runtime.anti_skill_v2_implementation_digest
        runtime.anti_skill_v2_implementation_digest = lambda: RETIRED_IMPLEMENTATION_DIGEST
        try:
            receipts = runtime.evaluate_antiskill_fixture_bank(_specs(), _bank())
        finally:
            runtime.anti_skill_v2_implementation_digest = current
        self.assertTrue(receipts.is_ok, receipts)
        produced = sorted(canonical_json_bytes(r.to_dict()) for r in receipts.unwrap())
        recorded = sorted(p.read_bytes() for p in CANARY.glob("*.evaluation-receipt.json"))
        self.assertEqual(len(recorded), 3)
        self.assertEqual(produced, recorded)

    def test_specs_bound_to_the_retired_source_bytes_are_refused(self):
        self.assertNotEqual(
            runtime.anti_skill_v2_implementation_digest(), RETIRED_IMPLEMENTATION_DIGEST
        )
        refused = runtime.evaluate_antiskill_fixture_bank(_specs(), _bank())
        self.assertTrue(refused.is_err)
        self.assertEqual(refused.unwrap_err().code, "ANTISKILL_EVALUATION_REFUSED")
        self.assertIn("implementation bytes", refused.unwrap_err().message)


if __name__ == "__main__":
    unittest.main()
