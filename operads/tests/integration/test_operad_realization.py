"""Exact existing native normal-form boundary, including negative controls."""
from copy import deepcopy
from dataclasses import replace

import pytest

from operations.domain.rop.result import Ok
from operads.contracts.operad_realization_v1 import (
    ModelBindingError, realize_native_result,
)
from operads.skill_operad.resolver.native_runtime import native_validate, run_native
from operads.skill_operad.resolver.resolver import digest
from operads.tests.integration.test_operad_native_runtime import inventory
from operads.skill_operad.skill_compiler.op_inventory import Wire


def nested():
    wire = Wire(op="pair", args=("Code", Wire(op="pair", args=("Code", "Code"))))
    return inventory(wire), wire


def test_actual_normal_form_preserves_all_fields_and_repeated_occurrences():
    inv, wire = nested()
    result = native_validate(inv, wire, input_order=(2, 0, 1))
    bound = realize_native_result(inv, wire, result, input_order=(2, 0, 1))
    value = bound.to_json()
    assert value["normal_form"] == result["normal_form"]
    assert value["native_term_id"] == result["term_id"]
    assert [x["path"] for x in value["occurrences"]] == [[1], []]
    assert [x["op_id"] for x in value["occurrences"]] == ["pair", "pair"]
    assert value["plan"] == result["execution_plan"]
    assert value["external_to_planar"] == [2, 0, 1]
    assert value["planar_to_external"] == [1, 2, 0]
    value["normal_form"]["boundary"]["inputs"].clear()
    assert len(bound.to_json()["normal_form"]["boundary"]["inputs"]) == 3


@pytest.mark.parametrize("change", ["port", "executor", "plan", "boundary", "order", "term", "wire", "guard", "operation_ids"])
def test_tampered_native_model_refuses_before_any_effect(change):
    inv, wire = nested()
    result = native_validate(inv, wire, input_order=(0, 1, 2))
    altered = deepcopy(result)
    tree = altered["normal_form"]["planar"]["tree"]
    if change == "port": tree["operation"]["input_ports"][0]["port_id"] = "different-provenance"
    elif change == "executor": tree["operation"]["executor_digest"] = "sha256:" + "a" * 64
    elif change == "plan": altered["execution_plan"][0]["args"].reverse()
    elif change == "boundary": altered["normal_form"]["boundary"]["inputs"][0]["schema_ref"] = "other"
    elif change == "order": altered["normal_form"]["external_to_planar"] = [True, 1, 2]
    elif change == "term": altered["term_id"] = "sha256:" + "a" * 64
    elif change == "wire": altered["request_binding"]["wire"]["args"].reverse()
    elif change == "guard": altered["execution_plan"][0]["guards"] = [{"op_id": "forged"}]
    else: altered["operation_ids"].pop()
    with pytest.raises(ModelBindingError):
        realize_native_result(inv, wire, altered, input_order=(0, 1, 2))
    class ForgedHost:
        def invoke_runtime(self, *_):
            return Ok({"success": True, "result": altered})
    calls = []
    receipt = run_native(inv, wire, [1, 2, 3], {"pair": lambda *args: calls.append(args)}, {}, host=ForgedHost(), input_order=(0, 1, 2))
    assert not receipt.completed and not calls and not receipt.steps


def test_identity_has_no_invocation_and_depth_three_realizations_are_finite():
    from operads.tests.integration.test_operad_native_runtime import binary_trees
    for wire in binary_trees(3):
        inv = inventory(wire)
        result = native_validate(inv, wire)
        model = realize_native_result(inv, wire, result).to_json()
        assert len(model["occurrences"]) == len(result["execution_plan"])
        if isinstance(wire, str):
            assert not model["occurrences"] and model["output_ref"] == {"input": 0}


def test_model_binding_retains_full_tree_but_receipt_only_executed_prefix():
    from operads.skill_operad.resolver.resolver import CheckedOccurrenceRejection
    inv, wire = nested()
    class Checker:
        def bind_native_model(self, model): self.model = model
        def __call__(self, snapshot):
            self.model.verify_invocation(snapshot)
            self.snapshot = snapshot
            return CheckedOccurrenceRejection(snapshot.digest(), "finite", "NEGATIVE", "a" * 64, '{}')
    checker = Checker()
    result = run_native(inv, wire, [1, 2, 3], {"pair": lambda a, b: [a, b]}, {}, occurrence_checker=checker)
    assert len(result.steps) == 1 and result.null_tree
    assert len(checker.model.to_json()["occurrences"]) == 2
    assert result.to_json()["schema"] == "core.oewas.run_receipt.v5"
    assert result.to_json()["native_model"] == checker.model.to_json()
    assert result.to_json()["native_model"]["input_digest"] == digest([1, 2, 3])
    with pytest.raises(ModelBindingError):
        checker.model.verify_invocation(replace(checker.snapshot, ordinal=1))
    with pytest.raises(ValueError):
        replace(result, native_term_id="other")


def test_unused_binding_retains_legacy_receipt_and_snapshot_profile():
    inv, wire = nested()
    result = run_native(inv, wire, [1, 2, 3], {"pair": lambda a, b: [a, b]}, {})
    assert result.completed and result.to_json()["schema"] == "core.oewas.run_receipt.v2"
    assert "native_model" not in result.to_json()


def test_nullary_model_and_model_binder_failure_have_no_invented_execution():
    from operads.skill_operad.skill_compiler.op_inventory import OpInventory, OpSpec, SkillDecomposition
    wire = Wire(op="constant")
    inv = OpInventory(schema_version="core.oewas.op_inventory.v3", skills=(
        SkillDecomposition(skill_id="constant", ops=(OpSpec(op_id="constant", summary="constant", output="Code"),), wiring=wire),))
    result = native_validate(inv, wire, input_order=())
    model = realize_native_result(inv, wire, result, input_order=()).to_json()
    assert model["root_inputs"] == [] and len(model["occurrences"]) == 1
    class BrokenBinder:
        def bind_native_model(self, _): raise RuntimeError("unavailable")
        def __call__(self, _): pytest.fail("checker should not run")
    receipt = run_native(inv, wire, [], {"constant": lambda: pytest.fail("executor should not run")}, {}, occurrence_checker=BrokenBinder())
    assert receipt.refusal.code == "OCCURRENCE_CHECK_UNAVAILABLE"
    assert receipt.null_tree is None and not receipt.steps


@pytest.mark.parametrize("mutation", ["wire", "input_order", "output", "interpreter_version"])
def test_completed_bound_receipt_cannot_disagree_with_embedded_request(mutation):
    inv, wire = nested()
    class Checker:
        def bind_native_model(self, model): self.model = model
        def __call__(self, snapshot): self.model.verify_invocation(snapshot)
    receipt = run_native(inv, wire, [1, 2, 3], {"pair": lambda a, b: [a, b]}, {}, occurrence_checker=Checker())
    assert receipt.completed
    changed = {"wire": "Code", "input_order": (2, 1, 0), "output": "counterfeit",
        "interpreter_version": "unrecorded-interpreter"}
    with pytest.raises(ModelBindingError):
        replace(receipt, **{mutation: changed[mutation]}).to_json()
