"""Explicit external-to-planar input order, with noncommutative controls."""
import itertools
from copy import deepcopy

import pytest

from operations.domain.rop.result import Ok
from operads.skill_operad.resolver.native_runtime import (
    NativeOperadRefusal,
    native_validate,
    run_native,
)
from operads.skill_operad.resolver.resolver import run
from operads.skill_operad.skill_compiler.op_inventory import (
    AntiOpSpec,
    HostBinding,
    OpInventory,
    OpSpec,
    SkillDecomposition,
    Wire,
)


def fixture(guard=False):
    wire = Wire(op="pair", args=("Code", Wire(op="pair", args=("Code", "Code"))))
    op = OpSpec(op_id="pair", summary="ordered pair", inputs=("Code", "Code"), output="Code", binding=HostBinding(target="native:pair"))
    guards = (AntiOpSpec(op_id="guard", summary="physical left operand", guards="pair", slot=0, inspects="Code", refusal="BLOCK"),) if guard else ()
    inv = OpInventory(schema_version="core.oewas.op_inventory.v3", skills=(SkillDecomposition(skill_id="test", ops=(op,), anti_ops=guards, wiring=wire),))
    return inv, wire


def test_oracle_explicit_order_routes_occurrences_and_binds_receipt():
    inv, wire = fixture()
    receipt = run(inv, wire, [10, 20, 30], {"pair": lambda a, b: [a, b]}, {}, input_order=(2, 0, 1))
    assert receipt.completed and receipt.output == [20, [30, 10]]
    assert receipt.to_json()["input_order"] == [2, 0, 1]
    assert receipt.to_json()["schema"] == "core.oewas.run_receipt.v3"
    legacy = run(inv, wire, [10, 20, 30], {"pair": lambda a, b: [a, b]}, {})
    assert "input_order" not in legacy.to_json()
    assert legacy.to_json()["schema"] == "core.oewas.run_receipt.v2"


@pytest.mark.parametrize("order", [(0, 0, 2), (0, 1), (0, 1, 3), (-1, 0, 1), (False, 1, 2), (0.0, 1, 2)])
def test_oracle_invalid_order_refuses_before_effect(order):
    inv, wire = fixture()
    calls = []
    receipt = run(inv, wire, [1, 2, 3], {"pair": lambda *a: calls.append(a)}, {}, input_order=order)
    assert receipt.refusal.code == "INVALID_INPUT_PERMUTATION" and not calls


def test_native_and_oracle_all_three_input_actions_and_guard_slots():
    inv, wire = fixture()
    for order in itertools.permutations(range(3)):
        values = [10, 20, 30]
        oracle = run(inv, wire, values, {"pair": lambda a, b: [a, b]}, {}, input_order=order)
        native = native_validate(inv, wire, values=values, input_order=order)
        runtime = run_native(inv, wire, values, {"pair": lambda a, b: [a, b]}, {}, input_order=order)
        assert runtime.completed
        assert native["output"] == runtime.output == oracle.output
        assert native["input_order"] == list(order)
        assert runtime.to_json()["input_order"] == list(order)
        assert runtime.native_term_id == native["term_id"]
    inv, wire = fixture(True)
    seen = []
    receipt = run_native(inv, wire, [10, 20, 30], {"pair": lambda a, b: [a, b]}, {"guard": lambda x: seen.append(x) or False}, input_order=(2, 0, 1))
    assert receipt.output == [20, [30, 10]] and seen == [30, 20]


def test_native_invalid_order_refuses_before_effect_and_identity_is_explicit():
    inv, wire = fixture()
    calls = []
    for order in ((0, 0, 2), (0, 1), (0, 1, 3), (-1, 0, 1), (False, 1, 2)):
        receipt = run_native(inv, wire, [1, 2, 3], {"pair": lambda *a: calls.append(a)}, {}, input_order=order)
        assert receipt.refusal is not None and not calls
    legacy = native_validate(inv, wire)
    explicit = native_validate(inv, wire, input_order=(0, 1, 2))
    assert "input_order" not in legacy
    assert explicit["term_id"] != legacy["term_id"]
    assert explicit["execution_plan"] == legacy["execution_plan"]


def test_explicit_mixed_colour_boundary_and_mapping_inputs():
    wire = Wire(op="pair", args=("Paper", "Code"))
    op = OpSpec(op_id="pair", summary="typed pair", inputs=("Paper", "Code"), output="State", binding=HostBinding(target="native:pair"))
    inv = OpInventory(schema_version="core.oewas.op_inventory.v3", skills=(SkillDecomposition(skill_id="test", ops=(op,), wiring=wire),))
    checked = native_validate(inv, wire, input_order=(1, 0), values=["program", "paper"])
    assert checked["leaves"] == ["Code", "Paper"]
    assert checked["output"] == ["paper", "program"]
    for runner in (run, run_native):
        result = runner(inv, wire, {"Code": "program", "Paper": "paper"}, {"pair": lambda a, b: [a, b]}, {}, input_order=(1, 0))
        assert result.completed and result.output == checked["output"]


def test_nullary_explicit_action_and_structural_identity():
    wire = Wire(op="sum", args=())
    op = OpSpec(op_id="sum", summary="nullary zero", inputs=(), output="Code", binding=HostBinding(target="native:sum"))
    inv = OpInventory(schema_version="core.oewas.op_inventory.v3", skills=(SkillDecomposition(skill_id="test", ops=(op,), wiring=wire),))
    assert native_validate(inv, wire, input_order=(), values=[])["output"] == 0
    assert run_native(inv, wire, [], {"sum": lambda: 0}, {}, input_order=()).output == 0
    assert run(inv, wire, [], {"sum": lambda: 0}, {}, input_order=()).output == 0
    assert run_native(inv, "Code", ["retained"], {}, {}, input_order=(0,)).output == "retained"


def test_stale_same_inventory_same_order_plan_refuses_before_dispatch():
    inv, wire = fixture()
    checked = native_validate(inv, wire, input_order=(2, 0, 1))
    class StaleHost:
        def invoke_runtime(self, action, payload):
            stale = deepcopy(checked)
            stale["request_binding"]["wire"] = "Code"
            stale["execution_plan"] = []
            stale["operation_ids"] = []
            stale["output_ref"] = {"input": 0}
            return Ok({"success": True, "result": stale})
    calls = []
    result = run_native(inv, wire, [1, 2, 3], {"pair": lambda *a: calls.append(a)}, {}, host=StaleHost(), input_order=(2, 0, 1))
    assert result.refusal.code == "NATIVE_OPERAD_BINDING" and not calls


def test_native_value_result_cannot_replay_for_different_input_values():
    inv, wire = fixture()
    checked = native_validate(inv, wire, values=[1, 2, 3], input_order=(2, 0, 1))
    class StaleHost:
        def invoke_runtime(self, action, payload):
            return Ok({"success": True, "result": deepcopy(checked)})
    with pytest.raises(NativeOperadRefusal, match="NATIVE_OPERAD_BINDING"):
        native_validate(inv, wire, values=[3, 2, 1], input_order=(2, 0, 1), host=StaleHost())
