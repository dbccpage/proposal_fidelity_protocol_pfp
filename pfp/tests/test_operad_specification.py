"""Adversarial metadata tests; no graph, quantum, signature or theorem solver runs."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pfp.domain.operad.specification import (
    ArchitectureSpec,
    parse_architecture_json,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "operad_specification"


@pytest.fixture
def reference():
    return json.loads((FIXTURES / "reference.json").read_text(encoding="utf-8"))


def parse(value):
    return parse_architecture_json(json.dumps(value, ensure_ascii=False))


def test_reference_json_yaml_and_schema_are_consistent(reference):
    model = parse(reference)
    yaml_reference = yaml.safe_load((FIXTURES / "reference.yaml").read_text(encoding="utf-8"))
    assert parse(yaml_reference) == model
    assert (
        json.loads((FIXTURES / "architecture_spec.schema.json").read_text())
        == ArchitectureSpec.model_json_schema()
    )
    assert (
        model.validation_effect
        == "source_bindings_and_metadata_only_no_theorem_signature_psd_confluence_or_runtime_acceptance"
    )
    assert (
        model.rg_steps[0].verification_status
        == "finite_partial_trace_declared_no_rg_or_channel_theorem_verified"
    )


def test_source_boundaries_are_utf8_bytes_not_characters(reference):
    model = parse(reference)
    assert model.sources[0].content_utf8 == "αβ\n"
    assert model.spans[0].end_byte == 2
    reference["spans"][0]["end_byte"] = 1
    with pytest.raises(ValidationError):
        parse(reference)


@pytest.mark.parametrize("field", ["source_sha256", "span_sha256"])
def test_source_span_hash_substitution_is_refused(reference, field):
    reference["spans"][0][field] = "f" * 64
    with pytest.raises(ValidationError):
        parse(reference)


def test_source_content_or_bound_changes_cannot_reuse_commitments(reference):
    changed = deepcopy(reference)
    changed["sources"][0]["content_utf8"] = "γβ\n"
    with pytest.raises(ValidationError):
        parse(changed)
    reference["spans"][0]["end_byte"] = 100
    with pytest.raises(ValidationError):
        parse(reference)


@pytest.mark.parametrize("alias", [True, 1.0, "1"])
def test_integer_byte_coordinates_reject_coercion_aliases(reference, alias):
    reference["spans"][0]["start_byte"] = alias
    with pytest.raises(ValidationError):
        parse(reference)


@pytest.mark.parametrize("token", [True, 0.5, 1, "0.5", "2/4", "1/1", " 1/2", "1/0"])
def test_scale_parameter_requires_exact_canonical_rational_string(reference, token):
    reference["rg_steps"][0]["scale_parameter"] = token
    with pytest.raises(ValidationError):
        parse(reference)


def test_unknown_fields_cannot_smuggle_verified_claims(reference):
    reference["densities"][0]["psd_verified"] = True
    with pytest.raises(ValidationError):
        parse(reference)


def test_metadata_and_nested_records_are_frozen(reference):
    model = parse(reference)
    with pytest.raises(ValidationError):
        model.spec_id = "changed"
    with pytest.raises(ValidationError):
        model.fibers[0].dimension = 9
    assert isinstance(model.trees[0].nodes, tuple)


@pytest.mark.parametrize("replacement", [[0, 0], [0, 2], [True, 0], [0]])
def test_invalid_or_boolean_input_permutations_are_refused(reference, replacement):
    reference["trees"][0]["nodes"][-1]["input_permutation"] = replacement
    with pytest.raises(ValidationError):
        parse(reference)


def test_actual_nominal_colour_typing_uses_permuted_children(reference):
    reference["colours"].append(
        {
            "colour_id": "raw_span_other",
            "payload_schema_artifact_id": "declarations",
            "interpretation_artifact_id": "declarations",
        }
    )
    reference["spans"][1]["colour"] = "raw_span_other"
    reference["trees"][0]["nodes"][1]["colour"] = "raw_span_other"
    reference["operators"][0]["input_colours"] = ["raw_span_other", "raw_span"]
    assert parse(reference).trees[0].nodes[-1].input_permutation == (1, 0)
    reference["trees"][0]["nodes"][-1]["input_permutation"] = [0, 1]
    with pytest.raises(ValidationError):
        parse(reference)


def test_undeclared_operator_colour_or_ideal_is_refused(reference):
    changed = deepcopy(reference)
    changed["operators"][0]["input_colours"][0] = "undeclared"
    with pytest.raises(ValidationError):
        parse(changed)
    reference["operators"][0]["ideal_ids"] = ["undeclared"]
    with pytest.raises(ValidationError):
        parse(reference)


def test_tree_topological_order_and_connectedness_are_required(reference):
    changed = deepcopy(reference)
    changed["trees"][0]["nodes"] = list(reversed(changed["trees"][0]["nodes"]))
    with pytest.raises(ValidationError):
        parse(changed)
    reference["trees"][0]["nodes"].insert(
        0, {"kind": "leaf", "node_id": "orphan", "span_id": "alpha", "colour": "raw_span"}
    )
    with pytest.raises(ValidationError):
        parse(reference)


def test_reusing_a_node_is_not_a_tree(reference):
    reference["trees"][0]["nodes"][-1]["children"] = ["a", "a"]
    with pytest.raises(ValidationError):
        parse(reference)


def test_graft_arity_and_duplicate_node_ids_are_refused(reference):
    changed = deepcopy(reference)
    changed["trees"][0]["nodes"][-1]["children"] = ["a"]
    with pytest.raises(ValidationError):
        parse(changed)
    reference["trees"][0]["nodes"][1]["node_id"] = "a"
    with pytest.raises(ValidationError):
        parse(reference)


def test_typed_null_tree_is_a_failure_record_not_a_density_matrix(reference):
    tree = reference["trees"][0]
    tree["nodes"] = [
        {
            "kind": "null_tree",
            "node_id": "null",
            "colour": "equation",
            "refusal_code": "KNOWN_DECOY",
            "evidence_artifact_id": "declarations",
        }
    ]
    tree["root"] = "null"
    model = parse(reference)
    assert model.trees[0].nodes[0].kind == "null_tree"
    assert model.densities[0].density_id == "fine_density"
    tree["nodes"].insert(
        0, {"kind": "leaf", "node_id": "unused", "span_id": "alpha", "colour": "raw_span"}
    )
    with pytest.raises(ValidationError):
        parse(reference)


def test_dpo_obligations_bind_all_artifacts_and_require_confluence_duties(reference):
    changed = deepcopy(reference)
    changed["dpo_declarations"][0]["right_artifact_id"] = "fine_matrix"
    with pytest.raises(ValidationError):
        parse(changed)
    reference["dpo_declarations"][0]["obligations"] = reference["dpo_declarations"][0][
        "obligations"
    ][:-1]
    with pytest.raises(ValidationError):
        parse(reference)


def test_owner_binding_cannot_point_to_unrelated_artifact(reference):
    reference["dpo_declarations"][0]["owner_source_artifact_id"] = "fine_matrix"
    with pytest.raises(ValidationError):
        parse(reference)


def test_density_declaration_never_claims_psd_or_reads_matrix(reference):
    # Rebinding to an arbitrary text artifact remains a declaration, never a
    # mathematical certificate. An actual backend must load and check it.
    density = reference["densities"][0]
    density["matrix_artifact_id"] = "declarations"
    for obligation in density["obligations"]:
        obligation["subject_artifact_ids"] = ["declarations"]
    reference["rg_steps"] = []
    model = parse(reference)
    assert (
        model.densities[0].verification_status
        == "matrix_not_loaded_hermiticity_trace_psd_not_verified"
    )
    density["verification_status"] = "verified"
    with pytest.raises(ValidationError):
        parse(reference)


def test_fiber_factor_product_and_partial_trace_target_are_bound(reference):
    changed = deepcopy(reference)
    changed["fibers"][0]["dimension"] = 5
    with pytest.raises(ValidationError):
        parse(changed)
    reference["rg_steps"][0]["trace_factor_id"] = "slow"
    with pytest.raises(ValidationError):
        parse(reference)


def test_partial_trace_channel_obligation_cannot_borrow_another_task(reference):
    reference["rg_steps"][0]["channel_laws"]["subject_artifact_ids"] = ["declarations"]
    with pytest.raises(ValidationError):
        parse(reference)


def test_signed_and_unsigned_receipt_metadata_stay_distinct(reference):
    receipt = reference["receipts"][0]
    receipt.update(
        {
            "kind": "signed_metadata",
            "algorithm": "Ed25519",
            "public_key_hex": "0" * 64,
            "signature_hex": "0" * 128,
            "signed_payload_artifact_id": "declarations",
            "trust_policy_artifact_id": "declarations",
            "verifier_source_artifact_id": "signature_owner",
        }
    )
    del receipt["signature_status"]
    model = parse(reference)
    assert model.receipts[0].signature_status == "supplied_not_cryptographically_verified"
    receipt["kind"] = "unsigned_benchmark"
    with pytest.raises(ValidationError):
        parse(reference)


def test_duplicate_json_keys_are_refused_before_pydantic_last_key_wins():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        parse_architecture_json('{"spec_id":"first","spec_id":"second"}')


@pytest.mark.parametrize("work_limit", [0, True, 1.5, "64"])
def test_operator_budget_requires_positive_strict_integer(reference, work_limit):
    reference["operators"][0]["work_limit"] = work_limit
    with pytest.raises(ValidationError):
        parse(reference)


def test_operator_effect_and_bundle_duties_are_explicit(reference):
    model = parse(reference)
    assert model.operators[0].effect_class == "pure"
    assert (
        model.bundles[0].verification_status
        == "declared_unverified_no_bundle_sheaf_or_gluing_theorem"
    )
    reference["operators"][0]["effect_class"] = "arbitrary_unclassified_effect"
    with pytest.raises(ValidationError):
        parse(reference)


@pytest.mark.parametrize("field, value", [("fiber_ids", ["unknown_fiber"]), ("rank", 5)])
def test_bundle_references_and_rank_are_checked_without_gluing(reference, field, value):
    reference["bundles"][0][field] = value
    with pytest.raises(ValidationError):
        parse(reference)


def test_bundle_cocycle_obligations_cannot_borrow_unbound_artifacts(reference):
    changed = deepcopy(reference)
    changed["bundles"][0]["cocycle_obligations"][0]["subject_artifact_ids"] = ["declarations"]
    with pytest.raises(ValidationError):
        parse(changed)
    reference["bundles"][0]["cocycle_obligations"] = reference["bundles"][0]["cocycle_obligations"][
        :2
    ]
    with pytest.raises(ValidationError):
        parse(reference)


def test_reference_artifact_hashes_match_the_audited_checkout(reference):
    root = Path(__file__).resolve().parents[2]
    for artifact in reference["artifacts"]:
        raw = (root / artifact["path"]).read_bytes()
        assert len(raw) == artifact["byte_length"]
        assert hashlib.sha256(raw).hexdigest() == artifact["sha256"]
