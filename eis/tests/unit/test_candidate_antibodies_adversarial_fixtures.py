"""Tests verifying formal candidate antibody YAML specifications against adversarial mutation fixtures.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from eis.domain import (
    ANTIBODY_TEMPLATES,
    Antibody,
    ConstraintType,
    PharmacySeeder,
    PharmacyStatus,
    RuntimeAction,
    Severity,
    classify_failure,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CANONICAL_SPECS_DIR = _REPO_ROOT / ".agents" / "antibodies" / "specs"
_LEGACY_SPECS_DIR = _REPO_ROOT / ".agents" / "oeeis" / "antibody_specs"
SPECS_DIR = _CANONICAL_SPECS_DIR if _CANONICAL_SPECS_DIR.is_dir() else _LEGACY_SPECS_DIR


def _load_yaml_spec(filename: str) -> dict[str, Any]:
    spec_path = SPECS_DIR / filename
    assert spec_path.is_file(), f"Specification file missing: {spec_path}"
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected dict in {filename}, got {type(data)}"
    return data


class TestCandidateAntibodiesFormalSpecifications:
    """Verifies that the YAML specifications conform to typed immune standards."""

    @pytest.mark.parametrize(
        "filename,expected_id,expected_class,expected_constraint,expected_action",
        [
            (
                "anti_floating_point_tolerance_leak.yaml",
                "anti-floating-point-tolerance-leak",
                "numerical:float_tolerance_leak",
                ConstraintType.PROJECT_OUT.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_implicit_credential_discovery.yaml",
                "anti-implicit-credential-discovery",
                "boundary:implicit_credential_discovery",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.ABORT.value,
            ),
            (
                "anti_limit_honesty_unhedged_claim.yaml",
                "ab_limit_honesty_unhedged_claim",
                "limit_honesty_violation",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_canonical_digest_ascii_drift.yaml",
                "ab_canonical_digest_ascii_drift",
                "digest:ensure_ascii_drift",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_fail_open_absent_gates.yaml",
                "ab_fail_open_absent_gates",
                "authority:absent_gates_admitted",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_cross_task_evidence_borrowing.yaml",
                "ab_cross_task_evidence_borrowing",
                "authority:cross_task_evidence_borrowing",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_silent_input_schema_coercion.yaml",
                "ab_silent_input_schema_coercion",
                "schema:silent_input_coercion",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
            (
                "anti_smuggled_custom_axiom_injection.yaml",
                "ab_smuggled_custom_axiom_injection",
                "mechanization:smuggled_custom_axiom",
                ConstraintType.RESTRAIN.value,
                RuntimeAction.REPAIR.value,
            ),
        ],
    )
    def test_yaml_specification_schema_and_authority(
        self,
        filename: str,
        expected_id: str,
        expected_class: str,
        expected_constraint: str,
        expected_action: str,
    ) -> None:
        spec = _load_yaml_spec(filename)

        assert spec["schema_version"] == "core.immune.antibody-spec.v1"
        assert spec["antibody_id"] == expected_id
        assert spec["failure_class"] == expected_class
        assert spec["constraint_type"] == expected_constraint
        assert spec["action"] == expected_action
        assert spec["severity"] == Severity.P0.value
        assert spec["pharmacy_status"] == PharmacyStatus.CANDIDATE.value
        assert spec["authority_effect"] == "None"

        # Check required fields
        assert spec["target_pattern"]
        assert spec["description"].strip()
        assert spec["adversarial_mutation_fixture"].strip()
        assert spec["repaired_invariant_fixture"].strip()
        assert len(spec["governing_invariants"]) >= 1


class TestAdversarialMutationFixtures:
    """Evaluates candidate antibodies against hostile specimens and repaired invariants."""

    @pytest.mark.parametrize(
        "filename",
        [
            "anti_floating_point_tolerance_leak.yaml",
            "anti_implicit_credential_discovery.yaml",
            "anti_limit_honesty_unhedged_claim.yaml",
            "anti_canonical_digest_ascii_drift.yaml",
            "anti_fail_open_absent_gates.yaml",
            "anti_cross_task_evidence_borrowing.yaml",
            "anti_silent_input_schema_coercion.yaml",
            "anti_smuggled_custom_axiom_injection.yaml",
        ],
    )
    def test_target_pattern_matches_hostile_and_misses_repair(self, filename: str) -> None:
        spec = _load_yaml_spec(filename)
        pattern = re.compile(spec["target_pattern"])
        hostile_matches = pattern.findall(spec["adversarial_mutation_fixture"])
        assert hostile_matches, "Expected target_pattern to match hostile specimen"
        repaired_matches = pattern.findall(spec["repaired_invariant_fixture"])
        assert repaired_matches == [], f"Repaired code triggered false positives: {repaired_matches}"

    def test_live_counterfeit_descent_does_not_match_fail_open_pattern(self) -> None:
        spec = _load_yaml_spec("anti_fail_open_absent_gates.yaml")
        pattern = re.compile(spec["target_pattern"])
        source = (
            Path(__file__).resolve().parents[3]
            / "atlas"
            / "coda_atlas"
            / "F004_papers"
            / "001_finite_obstruction_calculus"
            / "028_finite_authority_and_non_terminal_computation"
            / "code"
            / "mod_finite_authority_core.py"
        ).read_text(encoding="utf-8")
        start = source.index("def detect_counterfeit_descent")
        function = source[start:source.index("\nclass LGGRObstruction")]
        assert pattern.search(function) is None


class TestPharmacySeederIntegration:
    """Verifies that the new candidate antibodies integrate into PharmacySeeder and templates."""

    def test_classifier_recognizes_new_candidate_failure_classes(self) -> None:
        assert classify_failure("defect:float_tolerance_leak:core_types") == "float_tolerance_leak"
        assert classify_failure("defect:implicit_credential_discovery:openrouter") == "implicit_credential_discovery"
        assert classify_failure("defect:limit_honesty_violation:omc_dag") == "limit_honesty_violation"

    def test_templates_registered(self) -> None:
        assert "float_tolerance_leak" in ANTIBODY_TEMPLATES
        assert "implicit_credential_discovery" in ANTIBODY_TEMPLATES
        assert "limit_honesty_violation" in ANTIBODY_TEMPLATES

        float_tmpl = ANTIBODY_TEMPLATES["float_tolerance_leak"]
        assert float_tmpl.severity == Severity.P0.value
        assert float_tmpl.constraint_type == ConstraintType.PROJECT_OUT.value

        cred_tmpl = ANTIBODY_TEMPLATES["implicit_credential_discovery"]
        assert cred_tmpl.severity == Severity.P0.value
        assert cred_tmpl.constraint_type == ConstraintType.RESTRAIN.value

    def test_farm_candidate_antibodies_persists_to_disk(self, tmp_path: Path) -> None:
        seeder = PharmacySeeder(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)

        defects = [
            "defect:float_tolerance_leak:core_types.rational_bridge",
            "defect:implicit_credential_discovery:openrouter.adapter",
        ]

        farmed = seeder.farm_antibodies_from_defects(
            defects,
            run_id="run_mutation_adversarial_test",
            task_id="task_candidate_eval",
        )

        assert len(farmed) == 2
        for ab in farmed:
            assert isinstance(ab, Antibody)
            assert ab.pharmacy_status == PharmacyStatus.CANDIDATE.value
            assert ab.authority_effect == "None"
            assert ab.severity == "P0"

            # Check individual JSON record on disk (isolated in candidates subfolder)
            json_file = seeder.candidates_dir / f"{ab.antibody_id}.json"
            assert json_file.is_file(), f"Expected candidate isolated in candidates/: {json_file}"
            assert not (seeder.antibodies_dir / f"{ab.antibody_id}.json").exists(), (
                "Candidate antibody must not pollute root antibodies_dir"
            )

        # Check catalog on disk
        catalog = seeder.load_catalog()
        assert "antibodies" in catalog
        assert len(catalog["antibodies"]) == 2
