"""Antibody qualification test for candidate ab_limit_honesty_unhedged_claim.

Evaluates:
1. Typed schema compliance of anti_limit_honesty_unhedged_claim.yaml.
2. Adversarial mutation fixture sensitivity and repaired invariant specificity.
3. Thymic negative selection tolerance against clean reference self-fixtures.
4. Formal lifecycle boundary check in sovereign Rust kernel: determines whether
   and under what conditions formal checks can discharge its open obligation.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from omega_engine_epistemic_immune_system.domain import (
    ANTIBODY_TEMPLATES,
    ConstraintType,
    PharmacyStatus,
    RuntimeAction,
    Severity,
    classify_failure,
)
from omega_engine_epistemic_immune_system.domain.thymus import (
    CandidateDetector,
    ThymusGate,
)
from omega_engine_operations.infrastructure.intelligence_digestion import (
    NativeIntelligenceLifecycle,
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


class TestCandidateAntibodyQualification:
    """Qualification test suite for ab_limit_honesty_unhedged_claim."""

    def test_spec_schema_and_typing(self) -> None:
        spec = _load_yaml_spec("anti_limit_honesty_unhedged_claim.yaml")

        assert spec["schema_version"] == "omega.immune.antibody-spec.v1"
        assert spec["antibody_id"] == "ab_limit_honesty_unhedged_claim"
        assert spec["failure_class"] == "limit_honesty_violation"
        assert spec["constraint_type"] == ConstraintType.RESTRAIN.value
        assert spec["action"] == RuntimeAction.REPAIR.value
        assert spec["severity"] == Severity.P0.value
        assert spec["pharmacy_status"] == PharmacyStatus.CANDIDATE.value
        assert spec["authority_effect"] == "None"
        assert spec["target_pattern"]
        assert spec["description"].strip()
        assert spec["adversarial_mutation_fixture"].strip()
        assert spec["repaired_invariant_fixture"].strip()
        assert len(spec["governing_invariants"]) >= 1

    def test_pharmacy_templates_registration(self) -> None:
        assert "limit_honesty_violation" in ANTIBODY_TEMPLATES
        tmpl = ANTIBODY_TEMPLATES["limit_honesty_violation"]
        assert tmpl.constraint_type == ConstraintType.RESTRAIN.value
        assert tmpl.action == RuntimeAction.REPAIR.value
        assert tmpl.severity == Severity.P0.value
        assert classify_failure("defect:limit_honesty_violation:omc_dag") == "limit_honesty_violation"

    def test_adversarial_mutation_sensitivity_and_specificity(self) -> None:
        spec = _load_yaml_spec("anti_limit_honesty_unhedged_claim.yaml")
        pattern = re.compile(spec["target_pattern"])

        hostile_code = spec["adversarial_mutation_fixture"]
        repaired_code = spec["repaired_invariant_fixture"]

        # Sensitivity: hostile specimen must trigger the pattern
        hostile_matches = pattern.findall(hostile_code)
        assert len(hostile_matches) >= 1, "Expected target_pattern to match hostile specimen"

        # Specificity: repaired invariant code must NOT trigger the pattern
        repaired_matches = pattern.findall(repaired_code)
        assert len(repaired_matches) == 0, f"Repaired code triggered false positives: {repaired_matches}"

    def test_thymic_negative_selection_tolerance(self) -> None:
        spec = _load_yaml_spec("anti_limit_honesty_unhedged_claim.yaml")

        self_panel = (
            "# Clean reference fixture 1: Exact rational calculation\nfrom fractions import Fraction\nx = Fraction(1, 2)\n",
            "# Clean reference fixture 2: Bounded lattice model\ndef compute_chain(k: int) -> int:\n    return k * 2\n",
            "# Clean reference fixture 3: Hedged discrete state transition\ndef step(state: dict) -> dict:\n    return {'step': state.get('step', 0) + 1}\n",
        )

        thymus = ThymusGate(self_panel=self_panel)

        candidate = CandidateDetector(
            pattern=spec["target_pattern"],
            rule_id=spec["antibody_id"],
        )
        evaluation = thymus.evaluate_candidate(candidate)

        # Must be self-tolerant (0 autoimmune violations on clean reference self-fixtures)
        assert evaluation.self_tolerant is True
        # Must stay candidate (thymus does not self-certify admission)
        assert evaluation.is_admitted is False

    def test_formal_boundary_checks_discharge_determination(self) -> None:
        """Determines whether formal boundary checks can discharge its open obligation.

        In the sovereign Rust omega_intelligence kernel:
        1. An antibody in CANDIDATE status transferred from a run finding is an open
           obligation. Without a verified closure receipt, the finding transitions to
           state=ABSORBED, and remains listed in transferred_open_finding_ids.
        2. When formal qualification produces an exact verified ClosureReceipt,
           the obligation is satisfied and the lifecycle transitions to state=DISCHARGED.
        """
        lifecycle = NativeIntelligenceLifecycle()

        # 1. Manifest sealing
        sealed = lifecycle.seal_manifest(
            {
                "producer_id": "omega_research_papers",
                "source_class": "omc_dag_report",
                "source_locator": "_intelligence/omc_dags/omc_report_test.jsonl",
                "entries": [
                    {
                        "path": "omc_report_test.jsonl",
                        "size_bytes": 128,
                        "sha256": "sha256:" + hashlib.sha256(b'{"verdict":"NO_GO"}').hexdigest(),
                    }
                ],
            }
        )

        source_info = {
            "source_id": sealed["source_id"],
            "producer_id": sealed["producer_id"],
            "source_class": sealed["source_class"],
            "source_schema_version": sealed["schema_version"],
            "manifest_sha256": sealed["manifest_sha256"],
            "sealed": True,
            "producer_lease_active": False,
            "review_scope": "omega.qualification.limit_honesty.v1",
        }
        extraction_info = {
            "complete": True,
            "extractor_version": "omega.qualification.extractor.v1",
            "checker_version": "omega.qualification.checker.v1",
            "coverage_gaps": [],
            "parse_residuals": [],
        }

        finding_id = "finding:sha256:" + hashlib.sha256(b"LIMIT_HONESTY_VIOLATION").hexdigest()
        transfer_receipt = {
            "destination_id": "candidate_antibody:ab_limit_honesty_unhedged_claim",
            "target_revision": "sha256:" + "a" * 64,
            "acknowledgement_ref": "sha256:" + "b" * 64,
            "kind": "CANDIDATE_ANTIBODY_OPEN_OBLIGATION",
        }

        # Subtest A: Unclosed finding -> stays in state ABSORBED with open obligation
        unclosed_request = {
            "source": source_info,
            "extraction": extraction_info,
            "findings": [
                {
                    "finding_id": finding_id,
                    "kind": "OBSERVED_DEFECT_OR_OBLIGATION",
                    "applicable": True,
                    "transfer": transfer_receipt,
                    "closure": None,
                    "evidence_refs": [],
                }
            ],
        }
        unclosed_decision = lifecycle.evaluate_lifecycle(unclosed_request)

        assert unclosed_decision["state"] == "ABSORBED"
        assert unclosed_decision["archive_eligible"] is True
        assert finding_id in unclosed_decision["transferred_open_finding_ids"]
        assert unclosed_decision["certificate"]["kind"] == "ABSORPTION"

        # Subtest B: Closed finding with verified formal qualification ClosureReceipt -> DISCHARGED
        closure_ref = "sha256:" + hashlib.sha256(b"ab_limit_honesty_qualification_pass").hexdigest()
        closed_request = {
            "source": source_info,
            "extraction": extraction_info,
            "findings": [
                {
                    "finding_id": finding_id,
                    "kind": "OBSERVED_DEFECT_OR_OBLIGATION",
                    "applicable": True,
                    "transfer": transfer_receipt,
                    "closure": {
                        "checker_id": "checker:oeeis_thymus_gate",
                        "closure_ref": closure_ref,
                        "verified": True,
                    },
                    "evidence_refs": [],
                }
            ],
        }
        closed_decision = lifecycle.evaluate_lifecycle(closed_request)

        # Under verified closure, the open obligation is discharged!
        assert closed_decision["state"] == "DISCHARGED"
        assert closed_decision["archive_eligible"] is True
        assert closed_decision["transferred_open_finding_ids"] == []
        assert closed_decision["certificate"]["kind"] == "DISCHARGE"
