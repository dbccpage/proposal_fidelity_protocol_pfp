"""Unit tests for TrialStatusEnum dynamic YAML loading and taxonomy migration.

AuthorityEffect: None.
Verifies:
1. TrialStatusEnum members are loaded directly from YAML (omega_engine_pfp/infrastructure/yaml/taxonomy/trial_statuses.yaml).
2. TrialStatusEnum instances are strings and Enums simultaneously.
3. TrialStatusRegistry properly indexes all lifecycle states from YAML.
4. The taxonomy directory has been moved from yaml_data/taxonomy to yaml/taxonomy.
"""
from __future__ import annotations

import unittest
from enum import Enum
from pathlib import Path

import yaml

from omega_engine_pfp.infrastructure.taxonomy.trial_statuses import (
    TrialStatusDefinition,
    TrialStatusEnum,
    TrialStatusRegistry,
    VALID_TRIAL_STATUSES,
    get_valid_trial_statuses,
)

_INFRA_ROOT = Path(__file__).resolve().parents[2] / "infrastructure"


class TestTaxonomyTrialStatusesFromYaml(unittest.TestCase):
    """Test suite asserting TrialStatusEnum and taxonomy migration invariants."""

    def test_yaml_taxonomy_directory_migration(self) -> None:
        """Assert that yaml/taxonomy exists with all 9 files and yaml_data/taxonomy does not exist."""
        yaml_taxonomy = _INFRA_ROOT / "yaml" / "taxonomy"
        yaml_data_taxonomy = _INFRA_ROOT / "yaml_data" / "taxonomy"

        self.assertTrue(
            yaml_taxonomy.is_dir(),
            f"Expected {yaml_taxonomy} to exist and be a directory",
        )
        self.assertFalse(
            yaml_data_taxonomy.exists(),
            f"Expected {yaml_data_taxonomy} to have been moved to yaml/taxonomy",
        )

        expected_yaml_files = {
            "arithmetic_domains.yaml",
            "checkers.yaml",
            "claimed_moves.yaml",
            "evaluation_statuses.yaml",
            "execution_modes.yaml",
            "span_roles.yaml",
            "trial_statuses.yaml",
            "verification_rules.yaml",
            "verification_statuses.yaml",
        }
        present_files = {p.name for p in yaml_taxonomy.glob("*.yaml")}
        self.assertTrue(
            expected_yaml_files.issubset(present_files),
            f"Missing YAML files in {yaml_taxonomy}: {expected_yaml_files - present_files}",
        )

    def test_trial_status_enum_loaded_directly_from_yaml(self) -> None:
        """Assert that TrialStatusEnum members match exactly what is declared in trial_statuses.yaml."""
        yaml_file = _INFRA_ROOT / "yaml" / "taxonomy" / "trial_statuses.yaml"
        raw_data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        expected_ids = [item["id"] for item in raw_data["categories"]]

        enum_members = [m.value for m in TrialStatusEnum]
        self.assertEqual(
            enum_members,
            expected_ids,
            "TrialStatusEnum members must match the exact sequence declared in YAML",
        )

    def test_trial_status_enum_string_and_lookup_semantics(self) -> None:
        """Assert that TrialStatusEnum members behave as strings and proper enum instances."""
        for status_id in ("NOT_RUN", "RUNNING", "COMPLETED", "FAILED", "REFUSED", "PASS", "FAIL"):
            member = getattr(TrialStatusEnum, status_id)
            self.assertEqual(member.value, status_id)
            self.assertEqual(member, status_id)
            self.assertTrue(isinstance(member, str))
            self.assertIs(TrialStatusEnum(status_id), member)
            self.assertIs(TrialStatusEnum[status_id], member)

    def test_trial_status_registry_contents(self) -> None:
        """Assert that TrialStatusRegistry properly indexes definitions from YAML."""
        registry = TrialStatusRegistry.get_instance()
        all_ids = registry.all_ids()

        for status_id in ("NOT_RUN", "RUNNING", "COMPLETED", "FAILED", "REFUSED", "PASS", "FAIL"):
            self.assertTrue(registry.is_valid(status_id))
            self.assertIn(status_id, all_ids)
            defn = registry.get(status_id)
            self.assertIsNotNone(defn)
            self.assertIsInstance(defn, TrialStatusDefinition)
            self.assertEqual(defn.id, status_id)

        # Check terminal flags
        self.assertFalse(registry.get("NOT_RUN").is_terminal)
        self.assertFalse(registry.get("RUNNING").is_terminal)
        self.assertTrue(registry.get("COMPLETED").is_terminal)
        self.assertTrue(registry.get("FAILED").is_terminal)
        self.assertTrue(registry.get("REFUSED").is_terminal)
        self.assertTrue(registry.get("PASS").is_terminal)
        self.assertTrue(registry.get("FAIL").is_terminal)

    def test_module_level_helpers_and_constants(self) -> None:
        """Assert VALID_TRIAL_STATUSES and get_valid_trial_statuses()."""
        self.assertEqual(VALID_TRIAL_STATUSES, get_valid_trial_statuses())
        self.assertIn("RUNNING", VALID_TRIAL_STATUSES)
        self.assertIn("PASS", VALID_TRIAL_STATUSES)
        self.assertNotIn("NON_EXISTENT_STATUS", VALID_TRIAL_STATUSES)


if __name__ == "__main__":
    unittest.main()
