import pytest
from omega_engine_operads.domain.operad import ColouredOperad, OperationSignature, AgentSlice
from omega_engine_operads.skill_operad.meta_operad import OperadicEcology
from omega_engine_operads.domain.operad.errors import MissingUnitError


def test_identity_name_does_not_bypass_capability_slice():
    estate=ColouredOperad()
    estate.add_operation(OperationSignature.create("id_Code",["Code"],"Code"))
    assert estate.verify_agent_permission(AgentSlice("worker",set()),"id_Code").is_err
    with pytest.raises(MissingUnitError): estate.ensure_units()


def test_conflicting_registration_refuses():
    estate=ColouredOperad()
    estate.add_operation(OperationSignature.create("f",["Code"],"Code"))
    with pytest.raises(ValueError): estate.add_operation(OperationSignature.create("f",["Paper"],"Code"))


def test_declared_meta_operation_does_not_execute():
    assert OperadicEcology().execute("unknown")["code"]=="NOT_EXECUTABLE"



def test_offline_quotient_package_import_without_path_injection():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,"-c","import omega_engine_operads.skill_operad.quotient_operad"],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_symbolic_unit_table_is_not_unit_law_evidence_and_does_not_self_repair():
    from omega_engine_operads.skill_operad.coloured_operad import ColouredOperad as SymbolicRegistry, CompositionKey
    registry=SymbolicRegistry()
    registry.add_operation("f","F",["Code"],"Code")
    registry.ensure_units()
    assert registry.validate_units()==[]
    assert registry.unit_law_evidence()["status"]=="UNAVAILABLE"
    del registry.composition[CompositionKey("f",0,"id_Code")]
    before=dict(registry.composition)
    assert registry.validate_units()
    assert registry.composition==before
    registry.ensure_units()
    registry.operations["id_Code"].impl=lambda value:"counterfeit"
    assert registry.unit_law_evidence()["status"]=="UNAVAILABLE"
