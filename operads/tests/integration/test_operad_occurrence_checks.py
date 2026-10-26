"""Host-selected post-invocation checks; no model or provider calls."""
from dataclasses import FrozenInstanceError, replace
import json

import pytest

from omega_engine_operations.domain.rop.result import Ok
from omega_engine_operads.skill_operad.resolver.native_runtime import run_native
from omega_engine_operads.skill_operad.resolver.resolver import (
    CheckedOccurrenceRejection,
    ExecutionResult,
    InvocationSnapshot,
    digest,
    run,
)
from omega_engine_operads.skill_operad.skill_compiler.op_inventory import (
    AntiOpSpec, HostBinding, OpInventory, OpSpec, SkillDecomposition, Wire,
)


def fixture(guard=False):
    wire = Wire(op="finish", args=(Wire(op="pair", args=("Paper", "Code")),))
    ops = (
        OpSpec(op_id="pair", summary="pair", inputs=("Paper", "Code"), output="State", binding=HostBinding(target="external:pair")),
        OpSpec(op_id="finish", summary="finish", inputs=("State",), output="Audit", binding=HostBinding(target="external:finish")),
    )
    guards = (AntiOpSpec(op_id="guard", summary="guard", guards="pair", slot=0, inspects="Paper", refusal="BLOCK"),) if guard else ()
    inv = OpInventory(schema_version="omega.oewas.op_inventory.v3", skills=(
        SkillDecomposition(skill_id="test", ops=ops, anti_ops=guards, wiring=wire),))
    return inv, wire


def rejection(snapshot):
    return CheckedOccurrenceRejection(snapshot.digest(), "finite-gate", "CHECKED_NEGATIVE", "a" * 64, '{"task":"finite"}')


def test_rejected_child_retains_actual_step_and_exact_root_profile_before_parent():
    inv, wire = fixture()
    calls, snapshots = [], []
    def pair(left, right):
        calls.append("pair")
        return ExecutionResult((left, right), model="observed", usage={"output_tokens": 2}, cost_micro_usd=7)
    def checker(snapshot):
        snapshots.append(snapshot)
        return rejection(snapshot)
    result = run(inv, wire, ["paper", "code"], {"pair": pair, "finish": lambda value: calls.append("finish")}, {}, occurrence_checker=checker)
    assert calls == ["pair"] and not result.completed and result.output is None
    assert result.refusal.code == "CHECKED_OCCURRENCE_REJECTED"
    assert len(result.steps) == 1 and result.steps[0].execution["cost_micro_usd"] == 7
    assert result.null_tree.root_inputs == ("Paper", "Code") and result.null_tree.root_output == "Audit"
    assert result.null_tree.invocations == tuple(snapshots)
    assert result.null_tree.rejected_occurrences[0].invocation_digest == snapshots[0].digest()
    assert json.loads(snapshots[0].args_json) == ["paper", "code"]
    assert json.loads(snapshots[0].output_json) == ["paper", "code"]
    assert json.loads(snapshots[0].operation_json)["binding"]["target"] == "external:pair"
    assert json.loads(snapshots[0].execution_json)["cost_micro_usd"] == 7
    assert result.to_json()["schema"] == "omega.oewas.run_receipt.v4"
    assert result.to_json()["null_tree"]["root_inputs"] == ["Paper", "Code"]
    with pytest.raises(ValueError, match="stopped receipt"):
        replace(result, refusal=None)
    with pytest.raises(ValueError, match="stopped receipt"):
        replace(result, output="cannot return a rejected value")
    for binding in ("input_digest", "inventory_digest"):
        with pytest.raises(ValueError, match="exact run"):
            replace(result, **{binding: "b" * 64})
    with pytest.raises(ValueError, match="exact run"):
        replace(result, wire="Paper")
    with pytest.raises(ValueError, match="executed step"):
        replace(result, steps=(replace(result.steps[0], output_digest="b" * 64),))


def test_repeated_ids_have_distinct_actual_ordinals_and_checker_cannot_mutate_json():
    op = OpSpec(op_id="pair", summary="pair", inputs=("Code", "Code"), output="Code")
    wire = Wire(op="pair", args=("Code", Wire(op="pair", args=("Code", "Code"))))
    inv = OpInventory(schema_version="omega.oewas.op_inventory.v3", skills=(SkillDecomposition(skill_id="test", ops=(op,), wiring=wire),))
    seen = []
    def checker(snapshot):
        seen.append(snapshot)
        with pytest.raises(FrozenInstanceError):
            snapshot.ordinal = 8
        json.loads(snapshot.output_json).append("only a decoded copy")
    result = run(inv, wire, [1, 2, 3], {"pair": lambda a, b: (a, b)}, {}, input_order=(2, 0, 1), occurrence_checker=checker)
    assert result.completed and result.output == (2, (3, 1))
    assert [x.ordinal for x in seen] == [0, 1] and [x.op_id for x in seen] == ["pair", "pair"]
    assert seen[0].digest() != seen[1].digest()
    assert seen[0].input_order == (2, 0, 1) and seen[0].root_inputs == ("Code", "Code", "Code")
    assert result.to_json()["schema"] == "omega.oewas.run_receipt.v3"
    assert "null_tree" not in result.to_json()


def test_mutating_executor_keeps_pre_dispatch_operands_and_independent_output():
    inv, wire = fixture()
    seen = []
    left = {"value": "original"}
    def mutate(a, b):
        a["value"] = "changed by executor"
        return [a, b]
    def checker(snapshot):
        seen.append(snapshot)
        return rejection(snapshot)
    result = run(inv, wire, [left, "code"],
        {"pair": mutate, "finish": lambda _: pytest.fail("parent ran")}, {}, occurrence_checker=checker)
    assert left["value"] == "changed by executor"
    assert json.loads(seen[0].args_json) == [{"value": "original"}, "code"]
    assert json.loads(seen[0].output_json) == [{"value": "changed by executor"}, "code"]
    assert result.steps[0].input_digest == digest([{"value": "original"}, "code"])
    assert result.null_tree.invocations[0] == seen[0]


@pytest.mark.parametrize("bad", [False, {}, {"status": "REFUSE"}, "negative"])
def test_untyped_checker_reply_is_operational_invalid_without_bottom(bad):
    inv, wire = fixture()
    calls = []
    result = run(inv, wire, [1, 2], {"pair": lambda a, b: [a, b], "finish": lambda value: calls.append(value)}, {}, occurrence_checker=lambda snapshot: bad)
    assert result.refusal.code == "OCCURRENCE_CHECK_INVALID" and result.null_tree is None
    assert len(result.steps) == 1 and not calls and result.to_json()["schema"] != "omega.oewas.run_receipt.v4"


def test_checker_exception_is_unavailable_and_does_not_claim_a_checked_negative():
    inv, wire = fixture()
    def unavailable(snapshot):
        raise TimeoutError("checker timed out")
    result = run(inv, wire, [1, 2], {"pair": lambda a, b: [a, b], "finish": lambda _: pytest.fail("parent ran")}, {}, occurrence_checker=unavailable)
    assert result.refusal.code == "OCCURRENCE_CHECK_UNAVAILABLE" and result.null_tree is None
    assert len(result.steps) == 1


@pytest.mark.parametrize("mutation", ["binding", "scope", "snapshot"])
def test_stale_or_constructor_bypassed_checker_facts_cannot_create_bottom(mutation):
    inv, wire = fixture()
    def checker(snapshot):
        decision = rejection(snapshot)
        if mutation == "binding":
            return replace(decision, invocation_digest="b" * 64)
        if mutation == "scope":
            object.__setattr__(decision, "scope_json", '{"task": "finite"}')
        else:
            object.__setattr__(snapshot, "output_json", '["changed"]')
        return decision
    result = run(inv, wire, [1, 2], {"pair": lambda a, b: [a, b], "finish": lambda _: pytest.fail("parent ran")}, {}, occurrence_checker=checker)
    assert result.refusal.code == "OCCURRENCE_CHECK_INVALID" and result.null_tree is None


def test_guards_still_run_before_executor_and_occurrence_checker():
    inv, wire = fixture(True)
    result = run(inv, wire, [1, 2], {"pair": lambda *args: pytest.fail("executor ran"), "finish": lambda _: None}, {"guard": lambda _: True}, occurrence_checker=lambda _: pytest.fail("checker ran"))
    assert result.refusal.code == "BLOCK" and not result.steps and result.null_tree is None


def test_unused_port_preserves_exact_legacy_v2_v3_receipt_projection():
    inv, wire = fixture()
    executors = {"pair": lambda a, b: [a, b], "finish": lambda value: value}
    for order in (None, (1, 0)):
        old = run(inv, wire, [1, 2], executors, {}, input_order=order)
        unused = run(inv, wire, [1, 2], executors, {}, input_order=order, occurrence_checker=None)
        assert old.to_json() == unused.to_json() and "null_tree" not in old.to_json()
        assert old.to_json()["schema"] == ("omega.oewas.run_receipt.v2" if order is None else "omega.oewas.run_receipt.v3")


class StructuralHost:
    """Capture an actual native structural reply, then optionally corrupt its binding."""
    def __init__(self, inventory, *, stale=False):
        self.inventory = inventory
        self.stale = stale
        self.requests = []
    def invoke_runtime(self, action, payload):
        self.requests.append(payload)
        assert action == "workflow_graph" and "values" not in payload
        from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
        response = RustSymbolGameHost().invoke_runtime(action, payload)
        assert response.is_ok
        if self.stale:
            response.value["result"]["outcome"]["request_binding"]["wire"] = "Paper"
        return response


def test_checker_enabled_native_path_explicitly_binds_plan_and_actual_host_values():
    inv, wire = fixture()
    host = StructuralHost(inv)
    seen = []
    def checker(snapshot):
        seen.append(snapshot)
        return rejection(snapshot)
    kwargs = dict(host=host, occurrence_checker=checker)
    executors = {"pair": lambda a, b: [a, b], "finish": lambda _: pytest.fail("parent ran")}
    first = run_native(inv, wire, [1, 2], executors, {}, **kwargs)
    second = run_native(inv, wire, [3, 4], executors, {}, **kwargs)
    assert host.requests[0]["input_order"] == [0, 1] and "values" not in host.requests[0]
    assert first.null_tree.root_inputs == ("Paper", "Code") and first.null_tree.root_output == "Audit"
    assert seen[0].native_term_id.startswith("sha256:")
    assert seen[0].input_digest != seen[1].input_digest and seen[0].digest() != seen[1].digest()
    assert json.loads(seen[0].args_json) == [1, 2] and json.loads(seen[1].args_json) == [3, 4]
    assert second.to_json()["schema"] == "omega.oewas.run_receipt.v4"


def test_stale_same_inventory_native_plan_refuses_before_executor_or_check():
    inv, wire = fixture()
    result = run_native(inv, wire, [1, 2], {"pair": lambda *args: pytest.fail("executor ran"), "finish": lambda _: None}, {},
        host=StructuralHost(inv, stale=True), occurrence_checker=lambda _: pytest.fail("checker ran"))
    assert result.refusal.code == "NATIVE_OPERAD_BINDING" and not result.steps and result.null_tree is None


def test_actual_native_structural_plan_stops_checked_child_before_external_parent():
    inv, wire = fixture()
    seen = []
    def checker(snapshot):
        seen.append(snapshot)
        return rejection(snapshot)
    result = run_native(inv, wire, ["paper", "code"],
        {"pair": lambda a, b: [a, b], "finish": lambda _: pytest.fail("parent ran")}, {}, occurrence_checker=checker)
    assert result.refusal.code == "CHECKED_OCCURRENCE_REJECTED"
    assert result.null_tree.root_inputs == ("Paper", "Code") and result.null_tree.root_output == "Audit"
    assert result.native_term_id == seen[0].native_term_id and result.native_plan_digest
    assert result.input_order == (0, 1) and json.loads(seen[0].args_json) == ["paper", "code"]


def test_model_shaped_labels_do_not_select_a_checker_or_create_bottom():
    inv, wire = fixture()
    value = {"status": "REFUSE", "gate_id": "finite-gate", "checked_occurrence": True}
    result = run(inv, wire, [value, "code"], {"pair": lambda a, b: [a, b], "finish": lambda item: item}, {})
    assert result.completed and result.output == [value, "code"] and result.null_tree is None
    assert result.to_json()["schema"] == "omega.oewas.run_receipt.v2"


@pytest.mark.parametrize("field,value", [("ordinal", True), ("root_inputs", ["Paper", "Code"]), ("scope_json", "NaN")])
def test_new_immutable_contracts_reject_nonliteral_or_noncanonical_values(field, value):
    inv, wire = fixture()
    captured = []
    run(inv, wire, [1, 2], {"pair": lambda a, b: [a, b], "finish": lambda value: value}, {}, occurrence_checker=lambda s: captured.append(s))
    if field == "scope_json":
        with pytest.raises((TypeError, ValueError)):
            replace(rejection(captured[0]), scope_json=value)
    else:
        with pytest.raises((TypeError, ValueError)):
            replace(captured[0], **{field: value})
