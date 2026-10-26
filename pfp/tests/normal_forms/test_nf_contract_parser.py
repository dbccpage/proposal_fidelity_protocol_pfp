"""Unit tests for normal-form contract parser and standard validation.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from omega_engine_pfp.infrastructure.normal_forms.catalog import check_catalog
from omega_engine_pfp.infrastructure.normal_forms.contract_model import load_yaml
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import CONTRACTS_DIR
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import STANDARD_PATH


def _minimal_contract() -> dict:
    return {
        "schema_version": "smplx.nf.contract.v0",
        "contract_kind": "normal_form_contract",
        "identity": {
            "id": "nf.example.sample",
            "name": "Sample Normal Form",
            "short_name": "SNF",
            "version": "v0",
            "family": "shape",
        },
        "purpose": {
            "excludes_anomaly": "a repeated fact",
            "preserves_invariant": "one fact in one place",
            "protected_skeleton": ["heading"],
            "non_claims": ["does not imply authorization"],
        },
        "declarations_required": ["heading"],
        "validation_criteria": ["the heading is declared"],
        "terminal_routes": ["Accept", "RejectSample"],
        "terminal_route_map": {"Accept": "Preserve", "RejectSample": "Reject"},
        "authorization": {"authorized_by": None, "certified_implies_authorized": False},
        "definition": {
            "formal_statement": "A sample relvar stores one fact in one place.",
            "quadrilateral": {
                "qualifies_as_true_normal_form": False,
                "qualification_gap": "sample",
                "anomaly_exclusion": "a repeated fact",
                "lossless_join": {
                    "status": "declared_reconstruction",
                    "statement": "the declared parts recombine",
                },
                "dependency_preservation": {
                    "status": "declared_with_the_invariant",
                    "statement": "the invariant stays on the schema",
                },
                "syntactic_decision": {
                    "status": "declaration_decidable",
                    "statement": "the check reads the heading",
                },
            },
        },
    }


def _write(directory: Path, name: str, document: dict) -> None:
    (directory / name).write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )


class TestNfContractParser(unittest.TestCase):
    def test_catalog_matches_the_standard(self):
        findings = check_catalog(CONTRACTS_DIR, STANDARD_PATH)
        self.assertEqual(findings, [])

    def test_fifth_normal_form_membership_is_key_implication(self):
        document = load_yaml(CONTRACTS_DIR / "nf.classical.5nf.yaml")
        statement = document["definition"]["formal_statement"].lower()
        screen = document["definition"]["sufficient_key_component_test"]
        self.assertIn("candidate keys", statement)
        self.assertEqual(screen["strength"], "sufficient")
        self.assertFalse(screen["necessary"])

    def test_boyce_codd_records_the_preservation_gap(self):
        document = load_yaml(CONTRACTS_DIR / "nf.classical.bcnf.yaml")
        status = document["definition"]["quadrilateral"]["dependency_preservation"]["status"]
        self.assertEqual(status, "not_always")

    def test_domain_key_form_is_not_a_general_decision_procedure(self):
        document = load_yaml(CONTRACTS_DIR / "nf.classical.dknf.yaml")
        quad = document["definition"]["quadrilateral"]
        self.assertFalse(quad["qualifies_as_true_normal_form"])
        self.assertEqual(
            quad["syntactic_decision"]["status"], "undecidable_for_arbitrary_constraints"
        )

    def test_zero_normal_form_is_not_a_true_normal_form(self):
        document = load_yaml(CONTRACTS_DIR / "nf.classical.0nf.yaml")
        self.assertFalse(document["definition"]["quadrilateral"]["qualifies_as_true_normal_form"])

    def test_a_contract_without_a_pillar_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            del document["definition"]["quadrilateral"]["syntactic_decision"]
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("syntactic_decision", codes)

    def test_duplicate_ids_fail(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first = _minimal_contract()
            second = copy.deepcopy(first)
            second["identity"]["id"] = "nf.example.other"
            _write(tmp_path, "nf.example.sample.yaml", first)
            _write(tmp_path, "nf.example.other.yaml", second)
            twin = copy.deepcopy(first)
            _write(tmp_path, "nf.example.twin.yaml", twin)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("duplicate_id", codes)
            self.assertIn("id_filename_mismatch", codes)

    def test_authorization_cannot_be_implied(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["authorization"]["certified_implies_authorized"] = True
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("authorization", codes)

    def test_an_unmapped_terminal_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["terminal_routes"].append("MysteryRoute")
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("unmapped_terminal", codes)

    def test_invalid_schema_ref_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["schema_ref"] = "./nonexistent_schema.yaml"
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("invalid_schema_ref", codes)

    def test_unknown_top_level_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["unauthorized_experimental_field"] = "malformed"
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("unknown_field", codes)

    def test_misleading_active_status_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["identity"]["contract_status"] = "active"
            _write(tmp_path, "nf.example.sample.yaml", document)
            # Create index with nf.example.sample under draft
            index_doc = {
                "schema_version": "smplx.nf.contract.index.v0",
                "contracts": {"active": [], "draft": ["nf.example.sample"]},
            }
            (tmp_path / "index.yaml").write_text(yaml.safe_dump(index_doc), encoding="utf-8")
            codes = {
                finding.code
                for finding in check_catalog(tmp_path, STANDARD_PATH, tmp_path / "index.yaml")
            }
            self.assertIn("misleading_active_status", codes)

    def test_unsupported_verified_status_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            document = _minimal_contract()
            document["identity"]["verification_status"] = "verified"
            # No verifier_receipt in certification and no evidence_required
            _write(tmp_path, "nf.example.sample.yaml", document)
            codes = {finding.code for finding in check_catalog(tmp_path, STANDARD_PATH)}
            self.assertIn("unsupported_verified_status", codes)

    def test_migration_v0_to_v1_and_validation(self):
        from omega_engine_pfp.infrastructure.normal_forms.migrate_contract import (
            migrate_v0_to_v1,
        )
        from omega_engine_pfp.infrastructure.normal_forms.validate_v1 import (
            validate_contract_v1,
        )

        v0_doc = _minimal_contract()
        v1_doc = migrate_v0_to_v1(v0_doc)
        self.assertEqual(v1_doc["schema_version"], "smplx.nf.contract.v1")
        self.assertIn("classification", v1_doc)
        self.assertIn("extensions", v1_doc)
        findings = validate_contract_v1(v1_doc)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
