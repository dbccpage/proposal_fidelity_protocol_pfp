"""Unit tests asserting demo_runners and judge_audit configurations load directly from YAML.

AuthorityEffect: None.
Verifies:
1. demo_runners enums (PfpStageStatus, ProposalStatus, ExecutionAttestationMode) load from demo_statuses.yaml.
2. Evaluator claim hygiene forbidden words load from claim_hygiene.yaml.
3. judge_audit OUTCOME_CODES, REFUSAL_STATUS_WORDS, and VERDICT_WORDS load from audit_taxonomy.yaml.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from pfp.infrastructure.pilot_runners.gate_checks import (
    FORBIDDEN_WORDS as FORBIDDEN_WORDS_001,
)
from pfp.infrastructure.pilot_runners.declaration_checks import (
    FORBIDDEN_WORDS as FORBIDDEN_WORDS_002,
)
from pfp.infrastructure.pilot_runners.mssn_models import (
    ExecutionAttestationMode,
)
from pfp.infrastructure.pilot_runners.mssn_models import PfpStageStatus
from pfp.infrastructure.pilot_runners.mssn_models import ProposalStatus
from adversary.tests.pilots.judge_packet_audit.audit import OUTCOME_CODES
from adversary.tests.pilots.judge_packet_audit.leakage import VERDICT_WORDS
from adversary.tests.pilots.judge_packet_audit.static_analysis import REFUSAL_STATUS_WORDS

_INFRA_ROOT = Path(__file__).resolve().parents[2] / "infrastructure"
_DEMO_RUNNERS_YAML_DIR = _INFRA_ROOT / "yaml" / "demo_runners"
_JUDGE_AUDIT_YAML_DIR = _INFRA_ROOT / "yaml" / "judge_audit"


class TestDemoRunnersAndJudgeAuditYaml(unittest.TestCase):
    """Test suite asserting YAML-driven configurations for demo_runners and judge_audit."""

    def test_demo_runners_statuses_yaml(self) -> None:
        yaml_file = _DEMO_RUNNERS_YAML_DIR / "demo_statuses.yaml"
        self.assertTrue(yaml_file.is_file(), f"{yaml_file} must exist")
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

        expected_stage_statuses = [item["id"] for item in data["pfp_stage_statuses"]]
        self.assertEqual([m.value for m in PfpStageStatus], expected_stage_statuses)

        expected_proposal_statuses = [item["id"] for item in data["proposal_statuses"]]
        self.assertEqual([m.value for m in ProposalStatus], expected_proposal_statuses)

        expected_attestation_modes = [item["id"] for item in data["execution_attestation_modes"]]
        self.assertEqual([m.value for m in ExecutionAttestationMode], expected_attestation_modes)

        # Dual string-enum check
        for status in expected_stage_statuses:
            member = getattr(PfpStageStatus, status)
            self.assertEqual(member.value, status)
            self.assertEqual(member, status)
            self.assertIsInstance(member, str)
            self.assertIs(PfpStageStatus(status), member)

    def test_demo_runners_claim_hygiene_yaml(self) -> None:
        yaml_file = _DEMO_RUNNERS_YAML_DIR / "claim_hygiene.yaml"
        self.assertTrue(yaml_file.is_file(), f"{yaml_file} must exist")
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

        expected_words = data["forbidden_words"]
        self.assertEqual(FORBIDDEN_WORDS_001, expected_words)
        self.assertEqual(FORBIDDEN_WORDS_002, expected_words)
        self.assertIn("proves", FORBIDDEN_WORDS_001)
        self.assertIn("weaponized", FORBIDDEN_WORDS_001)

    def test_judge_audit_taxonomy_yaml(self) -> None:
        yaml_file = _JUDGE_AUDIT_YAML_DIR / "audit_taxonomy.yaml"
        self.assertTrue(yaml_file.is_file(), f"{yaml_file} must exist")
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

        self.assertEqual(OUTCOME_CODES, data["outcome_codes"])
        self.assertEqual(REFUSAL_STATUS_WORDS, frozenset(data["refusal_status_words"]))
        self.assertEqual(VERDICT_WORDS, frozenset(data["verdict_words"]))


if __name__ == "__main__":
    unittest.main()
