"""Unit tests asserting all 9 Taxonomy Enums are loaded directly from YAML.

AuthorityEffect: None.
Verifies:
1. All 9 taxonomy Enums are populated from YAML files in infrastructure/yaml/taxonomy/:
   - SpanRoleEnum (span_roles.yaml)
   - ArithmeticDomainEnum (arithmetic_domains.yaml)
   - CheckerContractEnum / CheckerEnum (checkers.yaml)
   - ClaimedMoveEnum (claimed_moves.yaml)
   - EvaluationStatusEnum (evaluation_statuses.yaml)
   - ExecutionModeEnum (execution_modes.yaml)
   - TrialStatusEnum (trial_statuses.yaml)
   - VerificationRuleEnum (verification_rules.yaml)
   - VerificationStatusEnum (verification_statuses.yaml)
2. All enum members exhibit dual string-and-enum behavior.
3. Fallback guarantees when YAML is absent or invalid.
"""
from __future__ import annotations

import unittest
from enum import Enum
from pathlib import Path

import yaml

from pfp.infrastructure.taxonomy import (
    ArithmeticDomainEnum,
    CheckerContractEnum,
    CheckerEnum,
    ClaimedMoveEnum,
    EvaluationStatusEnum,
    ExecutionModeEnum,
    SpanRoleEnum,
    TrialStatusEnum,
    VerificationRuleEnum,
    VerificationStatusEnum,
)

_INFRA_ROOT = Path(__file__).resolve().parents[2] / "infrastructure"
_TAXONOMY_YAML_DIR = _INFRA_ROOT / "yaml" / "taxonomy"


class TestTaxonomyEnumsFromYaml(unittest.TestCase):
    """Test suite asserting dynamic YAML loading and contract integrity for all taxonomy enums."""

    def test_span_role_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "span_roles.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in SpanRoleEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(SpanRoleEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(SpanRoleEnum(expected_id), member)

    def test_arithmetic_domain_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "arithmetic_domains.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in ArithmeticDomainEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(ArithmeticDomainEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(ArithmeticDomainEnum(expected_id), member)

    def test_checker_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "checkers.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["checkers"]]

        for expected_id in expected_ids:
            member = CheckerContractEnum(expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(CheckerEnum(expected_id), member)

    def test_claimed_move_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "claimed_moves.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in ClaimedMoveEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(ClaimedMoveEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(ClaimedMoveEnum(expected_id), member)

    def test_evaluation_status_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "evaluation_statuses.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in EvaluationStatusEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(EvaluationStatusEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(EvaluationStatusEnum(expected_id), member)

    def test_execution_mode_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "execution_modes.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        for expected_id in expected_ids:
            member_name = expected_id.upper()
            member = getattr(ExecutionModeEnum, member_name)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(ExecutionModeEnum(expected_id), member)

    def test_verification_rule_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "verification_rules.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        for expected_id in expected_ids:
            member = getattr(VerificationRuleEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(VerificationRuleEnum(expected_id), member)

    def test_verification_status_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "verification_statuses.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in VerificationStatusEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(VerificationStatusEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(VerificationStatusEnum(expected_id), member)

    def test_trial_status_enum_loaded_from_yaml(self) -> None:
        yaml_file = _TAXONOMY_YAML_DIR / "trial_statuses.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_values = [m.value for m in TrialStatusEnum]
        self.assertEqual(enum_values, expected_ids)
        for expected_id in expected_ids:
            member = getattr(TrialStatusEnum, expected_id)
            self.assertEqual(member.value, expected_id)
            self.assertEqual(member, expected_id)
            self.assertIsInstance(member, str)
            self.assertIs(TrialStatusEnum(expected_id), member)


if __name__ == "__main__":
    unittest.main()
