from operads.skill_operad.resolver.resolver import run
from operads.skill_operad.skill_compiler.op_inventory import OpInventory, OpSpec, SkillDecomposition, Wire, AntiOpSpec


def fixture(guard=None):
    op=OpSpec(op_id="pair", summary="ordered pair", inputs=("Code","Code"), output="Code")
    wire=Wire(op="pair",args=("Code","Code"))
    inv=OpInventory(schema_version="core.oewas.op_inventory.v2",skills=(SkillDecomposition(skill_id="test",ops=(op,),anti_ops=(guard,) if guard else (),wiring=wire),))
    return inv,wire


def test_repeated_colours_require_occurrences():
    inv,wire=fixture()
    r=run(inv,wire,{"Code":1},{"pair":lambda a,b:[a,b]}, {})
    assert r.refusal.code == "AMBIGUOUS_INPUT"
    r=run(inv,wire,[1,2],{"pair":lambda a,b:[a,b]}, {})
    assert r.completed and r.output == [1,2]
    assert r.to_json()["input_digest"]
    assert r.to_json()["inventory_digest"]


def test_bad_guard_slot_refuses_before_effect():
    inv,wire=fixture(AntiOpSpec(op_id="guard",summary="bad",guards="pair",slot=4,inspects="Code",refusal="BLOCK"))
    calls=[]
    r=run(inv,wire,{"Code":1},{"pair":lambda *a:calls.append(a)}, {"guard":lambda x:False})
    assert r.refusal.code == "GUARD_SLOT_INVALID" and not calls


def test_executor_and_detector_exceptions_are_typed():
    def fail(*a): raise RuntimeError("witness")
    inv,wire=fixture()
    r=run(inv,wire,[1,2],{"pair":fail},{})
    assert r.refusal.code == "EXECUTOR_FAILED"
    inv,wire=fixture(AntiOpSpec(op_id="guard",summary="guard",guards="pair",slot=0,inspects="Code",refusal="BLOCK"))
    r=run(inv,wire,[1,2],{"pair":fail},{"guard":fail})
    assert r.refusal.code == "DETECTOR_FAILED"


def test_inventory_host_coverage_and_bounded_skill_execution(tmp_path):
    from operads.skill_operad.resolver.executors import HOST_EXECUTORS, HOST_DETECTORS, executable_coverage
    from operads.skill_operad.skill_compiler.op_inventory import load_inventory, INVENTORY_PATH
    from pathlib import Path
    from operads.skill_operad.resolver.resolver import digest
    inventory=load_inventory(Path(INVENTORY_PATH))
    assert all(executable_coverage(inventory).values())
    def invoke(skill,values):
        s=next(s for s in inventory.skills if s.skill_id==skill)
        return run(inventory,s.wiring,values,HOST_EXECUTORS,HOST_DETECTORS)
    envelope="Supports: finite test. Does not support: general proof. Narrowest claim: fixture. Next test: mutation."
    r=invoke("glossa-claim-hygiene-linter",{"Paper":{"paper.md":envelope},"Code":{"a.py":"x=1"}})
    assert r.completed and r.output["status"]=="COMPLIANT"
    r=invoke("governance-test-isolation",{"Code":{"a.py":"x=1"},"State":{"tests/test_a.py":"assert 1"}})
    assert r.completed and r.output["status"]=="PASS"
    r=invoke("governance-test-isolation",{"Code":{"test_a.py":"import sys; sys.path.append('x')"},"State":{}})
    assert r.refusal.code=="TEST_SYS_PATH_HACK"
    source=tmp_path/"source";source.write_text("exact source")
    ledger=HOST_EXECUTORS["ara.bind_source_hashes"]({"paths":[str(source)],"omitted_variables":[]})
    r=invoke("adversarial-receipt-audit",{"State":{"paths":[str(source)],"omitted_variables":[]},"Audit":{"source_hashes":ledger["sources"]}})
    assert r.completed and r.output["status"]=="SOURCE_BINDINGS_MATCH"
    source.write_text("changed")
    assert HOST_DETECTORS["ara.refuse_unrecomputed_hash"](ledger)
    code={"a.py":"x = 1 # comment\n"}
    proposal=HOST_EXECUTORS["mnc.purge"](code)
    audit={"input_digest":digest(code),"output_digest":proposal["output_digest"],"findings_count":0}
    r=invoke("meta-no-comments",{"Code":code,"Audit":audit})
    assert r.completed and "comment" not in r.output["a.py"]
    assert code["a.py"].endswith("comment\n")


def test_structural_identity_and_planar_input_order():
    from operads.skill_operad.resolver.resolver import compose,Composition
    inv,wire=fixture()
    term=compose(inv,["Code"],"Code",max_ops=0)
    assert isinstance(term,Composition) and term.ops==()
    assert run(inv,term.wire,{"Code":[1,2]}, {},{}).output==[1,2]


def test_execution_accounting_is_bound_not_inferred():
    from operads.skill_operad.resolver.resolver import ExecutionResult
    inv,wire=fixture()
    r=run(inv,wire,[1,2],{"pair":lambda a,b:ExecutionResult([a,b],model="model",usage={"output_tokens":2},cost_micro_usd=42,context={"attempt":"a"})},{})
    assert r.steps[0].execution["cost_micro_usd"]==42
    assert r.steps[0].input_digest and r.steps[0].operation_digest
    changed=run(inv,wire,[2,1],{"pair":lambda a,b:[a,b]}, {})
    assert r.input_digest!=changed.input_digest


def test_executable_coverage_drops_when_executor_removed(monkeypatch):
    from pathlib import Path
    from operads.skill_operad.resolver.executors import HOST_EXECUTORS, executable_coverage
    from operads.skill_operad.skill_compiler.op_inventory import load_inventory, INVENTORY_PATH
    inv=load_inventory(Path(INVENTORY_PATH))
    before=executable_coverage(inv)
    from operads.skill_operad.resolver import executors
    reduced=dict(HOST_EXECUTORS)
    del reduced["glossa.report"]
    monkeypatch.setattr(executors,"HOST_EXECUTORS",reduced)
    after=executable_coverage(inv)
    assert sum(before.values())==5 and sum(after.values())==4
    assert not after["glossa-claim-hygiene-linter"]


def test_unadmitted_learned_guard_is_unavailable_not_cleared(monkeypatch):
    from operads.domain.anti_skills.anti_skill_v2 import AntiSkillSpecV2
    from operads.skill_operad.resolver.executors import AdmittedAntiSkillDetector
    from eis.domain.guard_activation import ActivationRefusal
    from eis.use_cases import guard_activation
    spec=AntiSkillSpecV2(spec_id="learned")
    def unavailable(*args,**kwargs):
        raise ActivationRefusal("NOT_EXTERNALLY_ADMITTED","no admission")
    monkeypatch.setattr(guard_activation,"activate_learned_guard",unavailable)
    detector=AdmittedAntiSkillDetector(spec,lambda text:None,profile_digest="sha256:"+"0"*64,subject_scope="code",sensor=object(),guard_state=object(),host_health=object())
    inv,wire=fixture(AntiOpSpec(op_id="guard",summary="learned",guards="pair",slot=0,inspects="Code",refusal="BLOCK",typed_contract_id="learned"))
    calls=[]
    result=run(inv,wire,["subject",2],{"pair":lambda *args:calls.append(args)},{"guard":detector})
    assert result.refusal.code=="DETECTOR_UNAVAILABLE"
    assert result.anti_ops_cleared==() and not calls
    assert result.guard_events[-1]["state"]=="NOT_EXTERNALLY_ADMITTED"
