"""Actual native kernel plus Python value oracle; no model calls."""
import pytest
from omega_engine_operads.skill_operad.skill_compiler.op_inventory import OpSpec, OpInventory, HostBinding, Wire, SkillDecomposition
from omega_engine_operads.skill_operad.resolver.native_runtime import native_validate, NativeOperadRefusal
from omega_engine_operads.skill_operad.resolver.resolver import run


def inventory(wire):
    ops=tuple(OpSpec(op_id=name,summary=name,inputs=inputs,output="Code",binding=HostBinding(target="native:"+target)) for name,inputs,target in (("pair",("Code","Code"),"pair"),("sum",("Code","Code"),"sum"),("identity",("Code",),"identity")))
    return OpInventory(schema_version="omega.oewas.op_inventory.v3",skills=(SkillDecomposition(skill_id="finite-controls",ops=ops,wiring=wire if isinstance(wire,Wire) else Wire(op="identity",args=(wire,))),))


def binary_trees(depth):
    """All 26 ordered one-colour pair trees of height at most three."""
    if depth == 0:
        return ["Code"]
    lower=binary_trees(depth-1)
    return ["Code"]+[Wire(op="pair",args=(left,right)) for left in lower for right in lower]


def test_finite_depth_three_value_tree_interface_and_order_differential():
    from omega_engine_operads.skill_operad.resolver.resolver import _wire_leaves, _wire_ops
    trees=binary_trees(3)
    assert len(trees)==26
    term_ids=set()
    for wire in trees:
        inv=inventory(wire)
        values=list(range(len(_wire_leaves(wire))))
        native=native_validate(inv,wire,values=values)
        oracle=run(inv,wire,values,{"pair":lambda a,b:[a,b]}, {})
        assert oracle.completed and native["output"]==oracle.output
        assert native["leaves"]==list(_wire_leaves(wire))
        assert native["operation_ids"]==list(_wire_ops(wire))
        assert native["normal_form"]["boundary"]["inputs"]
        assert len(native["execution_plan"])==len(list(_wire_ops(wire)))
        term_ids.add(native["term_id"])
    assert len(term_ids)==26


def test_runtime_dispatches_native_plan_without_python_tree_interpreter(monkeypatch):
    from omega_engine_operads.skill_operad.resolver import resolver
    from omega_engine_operads.skill_operad.resolver.native_runtime import run_native
    def forbidden(*args,**kwargs):
        raise AssertionError("runtime must not use the Python oracle")
    monkeypatch.setattr(resolver,"run",forbidden)
    wire=Wire(op="pair",args=("Code",Wire(op="pair",args=("Code","Code"))))
    inv=inventory(wire)
    seen=[]
    def pair(a,b):
        seen.append((a,b))
        return [a,b]
    result=run_native(inv,wire,[1,2,3],{"pair":pair},{})
    assert result.completed and result.output==[1,[2,3]]
    assert seen==[(2,3),(1,[2,3])]
    assert result.native_term_id and result.native_plan_digest
    assert result.interpreter_version=="omega.oewas.native-plan-host.v1"
    changed=run_native(inv,wire,[3,2,1],{"pair":pair},{})
    assert changed.native_term_id==result.native_term_id
    assert changed.input_digest!=result.input_digest


def test_bad_slot_colour_and_value_overflow_refuse():
    wire=Wire(op="pair",args=("Paper","Code"))
    with pytest.raises(NativeOperadRefusal,match="COLOUR|COLOR|BOUNDARY"): native_validate(inventory(wire),wire)
    wire=Wire(op="sum",args=("Code","Code"))
    with pytest.raises(NativeOperadRefusal,match="VALUE_OVERFLOW"): native_validate(inventory(wire),wire,values=[2**63-1,1])


def test_native_identity_is_structural_and_nullary_inputs_are_exact():
    wire=Wire(op="identity",args=("Code",))
    assert native_validate(inventory(wire),wire,values=[[1,2]])["output"]==[1,2]
    with pytest.raises(NativeOperadRefusal,match="MISSING_INPUT"): native_validate(inventory(wire),wire,values=[])
