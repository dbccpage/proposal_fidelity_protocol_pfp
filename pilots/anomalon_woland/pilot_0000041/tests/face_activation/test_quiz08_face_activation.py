"""Independent signed-boundary oracle, contract attacks, CLI and compiled mutations."""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
from itertools import permutations, product
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

PILOT = Path(__file__).resolve().parents[2]
RUNNER = Path(os.environ.get("PFP_PILOT_000016_UNDER_TEST", PILOT / "run.py"))
spec = importlib.util.spec_from_file_location("quiz08_under_test", RUNNER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def tri(weight=0):
    return {"task_id": "triangle1", "vertices": ["a", "b", "c"], "edges": [["a", "b"], ["a", "c"], ["b", "c"]],
            "potential_face": {"face_id": "face1", "vertices": ["a", "b", "c"]},
            "activity_encoding": "one_potential_face_binary_activity_v1",
            "state": {"revision": 0, "face_weight": weight, "payload": {"note": "retained"}},
            "adapter": {"scheme": "linear_activity_observables_v1", "mass_scale": "1/1", "drag_scale": "1/1"}}


def query(kind, **kw):
    return {"case_id": "case1", "kind": kind, **kw}


def boundary_oracle(t):
    a, b, c = t["potential_face"]["vertices"]
    signed_edges = {(b,c): 1, (a,c): -1, (a,b): 1}
    return [signed_edges.get(tuple(e), -signed_edges.get(tuple(reversed(e)), 0)) for e in t["edges"]]


def apply_oracle(t, chain):
    result = dict.fromkeys(t["vertices"], 0)
    for (a, b), coefficient in zip(t["edges"], chain, strict=True):
        result[a] -= coefficient
        result[b] += coefficient
    return [result[v] for v in t["vertices"]]


def pop(t):
    after = deepcopy(t["state"])
    after["face_weight"] = 1
    after["revision"] += 1
    return query("pop", event_id="event1", face_id="face1", before_state_sha256=m.digest(t["state"]),
                 after=after, lock=boundary_oracle(t))


def run_pop(t, q, grant=True):
    return m.answer_for(t, q, m.permission_for(t, q) if grant is True else grant)["data"]


def fixtures():
    for names, signs, face_sign in product(permutations("abc"), product((-1,1), repeat=3), (-1,1)):
        mapping = dict(zip("abc", names, strict=True))
        t = tri()
        t["vertices"] = list(names)
        t["edges"] = [[mapping[v] for v in (edge if sign == 1 else edge[::-1])]
                      for edge, sign in zip(t["edges"], signs, strict=True)]
        t["potential_face"]["vertices"] = [mapping[v] for v in ("abc" if face_sign == 1 else "acb")]
        yield t


def test_oriented_topology_and_signed_locks():
    total, accepted = 0, 0
    for t in fixtures():
        expected = boundary_oracle(t)
        z = m.complex_data(t)
        assert z["face_boundary"] == expected
        assert z["boundary_of_face_boundary"] == [0,0,0]
        assert (z["B1"]["rows"],z["B1"]["cols"]) == (3,3)
        for i in range(3):
            unit = [int(j == i) for j in range(3)]
            assert m.mv(z["B1"], unit) == apply_oracle(t, unit)
        assert z["B2"] == {"rows":3,"cols":0,"values":[[],[],[]]}
        assert z["B1B2"] == {"rows":3,"cols":0,"values":[[],[],[]]}
        q = pop(t)
        for chain in product((-1,0,1), repeat=3):
            altered = deepcopy(q)
            altered["lock"] = list(chain)
            result = run_pop(t, altered)
            assert (result["status"] == "EXECUTED") == (list(chain) == expected)
            total += 1
            accepted += result["status"] == "EXECUTED"
        result = run_pop(t,q)
        assert not result["before_lock"]["exact"] and result["before_lock"]["closed"]
        assert result["after_lock"]["filling"] == [1]
        after = deepcopy(t)
        after["state"] = q["after"]
        after_z = m.complex_data(after)
        assert after_z["B2"] == {"rows":3,"cols":1,"values":[[v] for v in expected]}
        assert after_z["B1B2"]["values"] == [[0],[0],[0]]
        assert result["actual_after"]["topology"] == after_z
        altered = deepcopy(q)
        altered["lock"] = [2*v for v in expected]
        assert run_pop(t,altered)["failed"] == ["unit_signed_lock"]
    assert (total,accepted) == (2592,96)


def test_chain_classification_and_unrelated_cycle():
    for weight, chain in product((0,1), product(range(-2,3), repeat=3)):
        t = tri(weight)
        c = list(chain)
        result = m.answer_for(t,query("chain",chain=c))["data"]
        boundary = apply_oracle(t,c)
        expected_exact = c == [0,0,0] if weight == 0 else c == [c[0],-c[0],c[0]]
        assert result["closed"] == (not any(boundary))
        assert result["exact"] == expected_exact
        assert result["boundary"] == boundary
        if result["exact"]:
            assert result["filling"] == ([] if weight == 0 else [c[0]])
    t = tri(1)
    t["vertices"] += ["d","e","f"]
    t["edges"] += [["d","e"],["e","f"],["f","d"]]
    unrelated = m.classify(t,[0,0,0,1,1,1])
    assert unrelated["closed"] and not unrelated["exact"]
    assert m.classify(t,[1,-1,1,0,0,0])["exact"]


def test_transition_contract_and_replay():
    t = tri()
    q = pop(t)
    for before, after in product((0,1), repeat=2):
        source = tri(before)
        candidate = pop(source)
        candidate["after"]["face_weight"] = after
        result = run_pop(source,candidate)
        assert (result["status"] == "EXECUTED") == ((before,after) == (0,1))
    assert run_pop(t,q,None)["failed"] == ["permission"]
    assert run_pop(t,q,m.permission_for(t,q,False))["failed"] == ["permission"]
    stale = m.permission_for(t,q)
    for key, value in [("task_id","other1"),("adapter",None)]:
        other = deepcopy(t)
        other[key] = value
        assert "permission" in run_pop(other,q,stale)["failed"]
    for change, reason in [
        (lambda a:a.update(face_id="otherface"),"target"),
        (lambda a:a.update(before_state_sha256="f"*64),"before"),
        (lambda a:a["after"].update(revision=99),"after"),
        (lambda a:a["after"]["payload"].update(note="changed"),"after")]:
        altered = deepcopy(q)
        change(altered)
        result = run_pop(t,altered)
        assert reason in result["failed"] and result["actual_after"] is None and result["state"] == t["state"]
    t["state"]["payload"]["n"] = 1
    q = pop(t)
    q["after"]["payload"]["n"] = True
    assert "after" in run_pop(t,q)["failed"]
    t,q = tri(),pop(tri())
    grant = m.permission_for(t,q)
    replay = query("replay",events=[q,q])
    result = m.answer_for(t,replay,[grant,grant])["data"]
    assert result["status"] == "REFUSED"
    assert [s["status"] for s in result["steps"]] == ["EXECUTED","REFUSED"]
    assert result["state"] == q["after"]
    assert set(result["steps"][1]["failed"]) == {"permission","before","inactive","after"}
    assert m.answer_for(t,query("replay",events=[q]),[grant])["data"]["status"] == "EXECUTED"
    refused_first = m.answer_for(t,replay,[None,grant])["data"]
    assert len(refused_first["steps"]) == 1 and refused_first["state"] == t["state"]
    current = deepcopy(t)
    current["state"] = deepcopy(q["after"])
    q2 = pop(current)
    assert "inactive" in run_pop(current,q2)["failed"]
    assert t == tri() and q == pop(tri())


def test_observables_comparisons_and_missing_assignments():
    for weight, mass, drag in product((0,1),(None,"0/1","2/3"),(None,"0/1","5/2")):
        t = tri(weight)
        t["adapter"]["mass_scale"],t["adapter"]["drag_scale"] = mass,drag
        result = m.observations(t)
        def expected(scale, weight=weight):
            value = None if scale is None else Q(scale)*weight
            return None if value is None else f"{value.numerator}/{value.denominator}"
        assert result["toy_mass"] == expected(mass) and result["toy_drag"] == expected(drag)
        assert result["toy_massless_no_drag"] == (None if None in (mass,drag) else Q(mass)*weight == Q(drag)*weight == 0)
    t = tri()
    t["adapter"] = None
    assert m.observations(t) == {"toy_mass":None,"toy_drag":None,"toy_massless_no_drag":None}
    assert m.answer_for(t,query("compare",other_state=tri(1)["state"]))["data"]["right_mass_vs_left"] is None
    for before,after in product((0,1),repeat=2):
        t = tri(before)
        result = m.answer_for(t,query("compare",other_state=tri(after)["state"]))["data"]
        assert result["right_mass_vs_left"] == after-before
        assert not result["transition_executed"] and result["state"] == t["state"]


def test_source_rows_and_physics():
    report = m.exercise_report()
    assert len(report["exercises"]) == 9 and len(report["source_vocabulary"]) == 7
    rows = {r["id"]:r for r in report["exercises"]}
    assert set(rows) == {f"P8.{i}" for i in range(1,5)} | {f"DRILL8.{i}" for i in range(1,6)}
    for row in rows.values():
        assert row["computed_answer"] == m.answer_for(row["task"],row["query"],row["permission"])
        assert row["computed_answer"]["authority_effect"] == "None"
        assert row["computed_answer"]["genesis_effect"] == "None" and row["computed_answer"]["realizes"] is None
    assert rows["P8.1"]["computed_answer"]["data"]["observables"]["toy_massless_no_drag"] is True
    assert rows["P8.2"]["computed_answer"]["data"]["status"] == "EXECUTED"
    assert rows["DRILL8.2"]["task"]["state"]["face_weight"] == 0
    assert rows["P8.3"]["computed_answer"]["data"]["right_mass_vs_left"] == 1
    assert rows["DRILL8.4"]["computed_answer"]["data"]["observables"]["toy_drag"] == "1/1"
    for claim in ("cern_higgs_boson_125_gev","standard_model","origin_of_inertial_mass_in_qft"):
        for weight,assigned in product((0,1),(False,True)):
            t = tri(weight)
            if not assigned:
                t["adapter"] = None
            data = m.answer_for(t,query("physics",claim=claim))["data"]
            assert data["status"] == "REFUSED" and data["refusal"] == "ref<3>"
    report["source_vocabulary"].clear()
    assert len(m.exercise_report()["source_vocabulary"]) == 7


@pytest.mark.parametrize("edit",[
    lambda t:t.update(extra=0),lambda t:t.update(task_id=True),lambda t:t.update(vertices="abc"),
    lambda t:t.update(vertices=["a","a","c"]),lambda t:t.update(vertices=["a"]*17),
    lambda t:t.update(edges="abc"),lambda t:t["edges"].append(["b","a"]),lambda t:t["edges"].append(["x","y"]),
    lambda t:t["edges"].append(["a","a"]),lambda t:t["edges"].append(["a"]),lambda t:t["edges"].append([True,"a"]),
    lambda t:t["edges"].__setitem__(0,["b","d"]),lambda t:t["vertices"].append("d") or t["edges"].__setitem__(0,["a","d"]),
    lambda t:t.update(activity_encoding="face_weight_only"),
    lambda t:t["potential_face"].update(vertices=["a","b"]),lambda t:t["potential_face"].update(vertices=["a","a","c"]),
    lambda t:t["potential_face"].update(vertices=["a","b","d"]),lambda t:t["potential_face"].update(vertices=[[],[],[]]),
    lambda t:t["potential_face"].update(face_id=""),lambda t:t["state"].update(face_weight=True),
    lambda t:t["state"].update(face_weight=0.0),lambda t:t["state"].update(face_weight=2),
    lambda t:t["state"].update(revision=-1),lambda t:t["state"].update(revision=True),
    lambda t:t["state"].update(revision=1000001),lambda t:t["state"].update(payload=[]),
    lambda t:t["state"]["payload"].update(value=1.2),lambda t:t["adapter"].update(scheme="unknown"),
    lambda t:t["adapter"].update(mass_scale="-1/1"),lambda t:t["adapter"].update(drag_scale=True),
])
def test_bad_tasks(edit):
    t = tri()
    edit(t)
    with pytest.raises(m.InvalidInput):
        m.answer_for(t,query("observe"))


@pytest.mark.parametrize("value",["1","1/0","1/01","02/3","2/4","-1/1","1000001/1","1/1000001",0,True,None,[], "0/2"])
def test_bad_rationals(value):
    with pytest.raises(m.InvalidInput):
        m.rational(value)


@pytest.mark.parametrize("kind,values",[
    ("missing",{}),("observe",{"extra":0}),("chain",{"chain":[1]}),("chain",{"chain":[True,0,0]}),
    ("chain",{"chain":[1000001,0,0]}),("physics",{"claim":"unrestricted natural-language statement"}),
    ("replay",{"events":[]}),("replay",{"events":"bad"}),("replay",{"events":[pop(tri())]*9}),
])
def test_bad_queries(kind,values):
    with pytest.raises(m.InvalidInput):
        m.answer_for(tri(),query(kind,**values))


def test_bad_pop_permissions_and_replay_shapes():
    t,q = tri(),pop(tri())
    for grant in [{},[],{"permit_id":"x","admitted":1,"problem_sha256":"0"*64},
                  {"permit_id":"x","admitted":True,"problem_sha256":"X"*64}]:
        with pytest.raises(m.InvalidInput):
            run_pop(t,q,grant)
    for update in [dict(kind="observe"),dict(lock=[0]),dict(before_state_sha256=3),dict(event_id=True),dict(after={})]:
        altered = dict(q,**update)
        with pytest.raises(m.InvalidInput):
            m.answer_for(t,query("replay",events=[altered]),[None])
    for grant in [None,[],[None,None]]:
        with pytest.raises(m.InvalidInput):
            m.answer_for(t,query("replay",events=[q]),grant)
    for bad in [{},[],{"case_id":True,"kind":"observe"},{"case_id":"ok","kind":False}]:
        with pytest.raises(m.InvalidInput):
            m.answer_for(t,bad)
    with pytest.raises(m.InvalidInput):
        m.answer_for(t,query("observe"),m.permission_for(t,q))
    with pytest.raises(m.InvalidInput):
        m.mv({"cols":1,"values":[[1]]},[])


def test_unreached_permission_schema():
    t,q = tri(),pop(tri())
    replay = query("replay",events=[q,q])
    for bad in [{"unknown_schema_field":1},{},1,[],
                {"permit_id":"x","admitted":1,"problem_sha256":"0"*64},
                {"permit_id":"x","admitted":True,"problem_sha256":"bad"}]:
        with pytest.raises(m.InvalidInput):
            m.answer_for(t,replay,[None,bad])
    for valid in [None,m.permission_for(t,q),m.permission_for(t,q,False)]:
        answer = m.answer_for(t,replay,[None,valid])
        assert answer["data"]["status"] == "REFUSED"
        assert len(answer["data"]["steps"]) == 1 and answer["data"]["state"] == t["state"]
        assert m.evaluate(m.submission(t,replay,answer,[None,valid]))["verdict"] == "MATCH"


def test_binding_snapshot_and_forged_answers():
    t,q = tri(),pop(tri())
    grant = m.permission_for(t,q)
    answer = m.answer_for(t,q,grant)
    doc = m.submission(t,q,answer,grant)
    before = deepcopy(doc)
    assert m.evaluate(doc)["verdict"] == "MATCH"
    for mutation in [
        lambda d:d["query"].update(case_id="another"),lambda d:d["task"].update(task_id="another"),
        lambda d:d["permission"].update(permit_id="another"),lambda d:d["proposal"].update(input_sha256="0"*64),
        lambda d:d["proposal"]["answer"].update(authority_effect="Granted"),
        lambda d:d["proposal"]["answer"]["data"]["state"]["payload"].update(note="false"),
        lambda d:d["proposal"].update(answer={"status":"executed"}),
    ]:
        altered = deepcopy(doc)
        mutation(altered)
        assert m.evaluate(altered)["verdict"] == "MISMATCH"
    answer["data"]["state"]["payload"]["note"] = "changed"
    t["state"]["payload"]["note"] = "changed"
    grant["admitted"] = False
    assert doc == before
    result = m.evaluate(doc)
    result["inputs"]["task"]["state"]["payload"]["note"] = "mutated"
    assert doc == before
    with pytest.raises(m.InvalidInput):
        m.evaluate(dict(doc,extra=0))
    with pytest.raises(m.InvalidInput):
        m.evaluate(dict(doc,proposal={}))
    huge = m.submission(tri(),query("observe"),{"values":["x"*2048]*65})
    with pytest.raises(m.InvalidInput,match="byte limit"):
        m.evaluate(huge)


@pytest.mark.parametrize("raw",[b'',b'{"a":1,"a":2}',b'NaN',b'Infinity',b'not json',b'\xff',b'x'*131073,"wrong"],
                         ids=["empty","duplicate","nan","infinity","syntax","encoding","oversize","not_bytes"])
def test_decode_rejected(raw):
    with pytest.raises((ValueError,UnicodeError)):
        m.decode(raw)


@pytest.mark.parametrize("value",[1.2,object(),{"a":"x"*2049},{"a":"\n"},{1:2},[0]*257,{str(i):0 for i in range(65)},10**19])
def test_bad_json(value):
    with pytest.raises(m.InvalidInput):
        m.json_value(value)


def test_depth_and_helpers():
    nested = 0
    for _ in range(18):
        nested = [nested]
    with pytest.raises(m.InvalidInput):
        m.json_value(nested)
    m.json_value({"a":True,"b":None,"c":[1,"ok",{}]})
    assert m.decode(b'{"a":1}') == {"a":1}
    assert m.rational("2/3") == Q(2,3)
    assert m.triangle_task() == tri()
    assert m.pop_query(tri(),"case1") == pop(tri())


def verify_run(folder, raw=None):
    receipt = json.loads((folder/"receipt.json").read_text())
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["code_sha256"] == hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert set(receipt["artifact_sha256"]) == {"input.bin","result.json","summary.md"}
    for name,value in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == value
    if raw is not None:
        assert (folder/"input.bin").read_bytes() == raw
    return receipt,json.loads((folder/"result.json").read_text())


def test_inprocess_cli(tmp_path,capsys):
    outputs = []
    for _ in range(2):
        assert m.main(["--output-dir",str(tmp_path/"runs")]) == 0
        outputs.append(Path(json.loads(capsys.readouterr().out)["output"]))
        receipt,result = verify_run(outputs[-1])
        assert receipt["status"] == "DEMONSTRATED" and result == m.exercise_report()
    assert outputs[0] != outputs[1]
    before = {p.name:p.read_bytes() for p in outputs[0].iterdir()}
    source = tmp_path/"input.json"
    t,q = tri(),query("observe")
    for document,wanted in [({},1),(m.submission(t,q,{"forged":True}),1),(m.submission(t,q,m.answer_for(t,q)),0)]:
        raw = json.dumps(document,indent=2).encode()
        source.write_bytes(raw)
        assert m.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")]) == wanted
        verify_run(Path(json.loads(capsys.readouterr().out)["output"]),raw)
    for raw in (b"NaN",b"x"*131073):
        source.write_bytes(raw)
        assert m.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")]) == 2
        assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert m.main(["--input",str(tmp_path/"absent")]) == 2
    capsys.readouterr()
    occupied = tmp_path/"occupied"
    occupied.write_text("keep")
    assert m.main(["--output-dir",str(occupied)]) == 2
    capsys.readouterr()
    assert occupied.read_text() == "keep"
    assert {p.name:p.read_bytes() for p in outputs[0].iterdir()} == before


@pytest.mark.parametrize("kind",["observe","chain","compare","pop","replay","physics"])
def test_real_cli(tmp_path,kind):
    t = tri()
    extra = {"chain":[1,-1,1]} if kind == "chain" else {"other_state":tri(1)["state"]} if kind == "compare" else (
        {"claim":"standard_model"} if kind == "physics" else {})
    q,grant = query(kind,**extra),None
    if kind == "pop":
        q = pop(t)
        grant = m.permission_for(t,q)
    elif kind == "replay":
        event = pop(t)
        q = query("replay",events=[event,event])
        grant = [m.permission_for(t,event)]*2
    document = m.submission(t,q,m.answer_for(t,q,grant),grant)
    raw = json.dumps(document,indent=1).encode()
    source = tmp_path/"input.json"
    source.write_bytes(raw)
    result = subprocess.run([sys.executable,str(RUNNER),"--input",str(source),"--output-dir",str(tmp_path/"runs")],
                            capture_output=True,text=True,check=False)
    assert result.returncode == 0,result.stdout+result.stderr
    receipt,report = verify_run(Path(json.loads(result.stdout)["output"]),raw)
    assert receipt["status"] == "MATCH" and report["canonical"] == document["proposal"]["answer"]


MUTATIONS = (
    ("skip_unreached_grant_schema","            permission_shape(grant)","            pass","test_unreached_permission_schema"),
    ("endpoint_sign","int(v == b) - int(v == a)","int(v == b) + int(v == a)","test_oriented_topology"),
    ("face_sign","boundary[j] = 1 if edges[j] == [u, v] else -1","boundary[j] = 1","test_oriented_topology"),
    ("inactive_face_present",'active = task["state"]["face_weight"] == 1',"active = True","test_oriented_topology"),
    ("inactive_exact", 'witness = [] if not any(chain) else None', 'witness = []', "test_chain_classification"),
    ("all_closed_fill", 'chain == [k*value for value in face_boundary]', 'not any(boundary)', "test_chain_classification"),
    ("any_closed_lock",'query["lock"] == topology["face_boundary"]','not any(mv(topology["B1"], query["lock"]))',"test_oriented_topology"),
    ("missing_permission",'allowed = permission_valid(task, query, permission)','allowed = True',"test_transition_contract"),
    ("stale_permission",'permission["problem_sha256"] == digest({"task": task, "query": query})','True',"test_transition_contract"),
    ("wrong_target", 'query["face_id"] == task["potential_face"]["face_id"]','True',"test_transition_contract"),
    ("repeat_pop",'task["state"]["face_weight"] == 0,','True,',"test_transition_contract"),
    ("payload_equality",'encoded(query["after"]) == encoded(expected_after)','query["after"] == expected_after',"test_transition_contract"),
    ("replay_frozen_state",'task["state"] = clone(step["state"])','pass',"test_transition_contract"),
    ("default_assignment",'None if scale is None else qtext(rational(scale)*weight)','"0/1" if scale is None else qtext(rational(scale)*weight)',"test_observables"),
    ("observable_ignores_weight",'qtext(rational(scale)*weight)','qtext(rational(scale))',"test_observables"),
    ("physical_promotion",'"refusal": "ref<3>"','"refusal": None',"test_source_rows"),
    ("authority_promotion",'"case_id": query["case_id"], "kind": kind, "data": data,\n            "authority_effect": "None"','"case_id": query["case_id"], "kind": kind, "data": data,\n            "authority_effect": "Granted"',"test_source_rows"),
    ("proposal_binding",'binding_ok and encoded(proposal["answer"]) == encoded(canonical)','encoded(proposal["answer"]) == encoded(canonical)',"test_binding_snapshot"),
    ("always_match",'matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)','matches = True',"test_binding_snapshot"),
    ("duplicate_json",'require(key not in result,','require(True,',"test_decode_rejected"),
    ("noncanonical_rational",'require(qtext(parsed) == value,','require(True,',"test_bad_rationals"),
)


def test_implementation_mutations(tmp_path):
    if os.environ.get("PFP_PILOT_000016_UNDER_TEST"):
        return
    original_raw = RUNNER.read_bytes()
    source = RUNNER.read_text(encoding="utf-8")
    rows = []
    for name,anchor,replacement,selection in MUTATIONS:
        assert source.count(anchor) == 1,(name,source.count(anchor))
        assert anchor != replacement
        mutant = source.replace(anchor,replacement)
        compile(mutant,name,"exec")
        target = tmp_path/(name+".py")
        target.write_text(mutant,encoding="utf-8",newline="\n")
        xml = tmp_path/(name+".xml")
        env = dict(os.environ,PFP_PILOT_000016_UNDER_TEST=str(target),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONDONTWRITEBYTECODE="1")
        child = subprocess.run([sys.executable,"-m","pytest",str(Path(__file__).resolve()),"-q","-p","no:cacheprovider","-o","addopts=",
                                "--import-mode=importlib","--basetemp",str(tmp_path/(name+"_tmp")),"--junitxml",str(xml),"-k",selection],
                               capture_output=True,text=True,env=env,check=False)
        failures = [case.attrib["name"] for case in ET.parse(xml).iter("testcase") if case.find("failure") is not None]
        assert child.returncode == 1 and failures,(name,child.stdout,child.stderr)
        assert RUNNER.read_bytes() == original_raw
        rows.append({"name":name,"target":"run.py","anchor":anchor,"replacement":replacement,"selection":selection,
                     "applied":True,"exit_code":child.returncode,"failed_nodes":failures,"original_unchanged":True,
                     "original_sha256":hashlib.sha256(original_raw).hexdigest(),"mutant_sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    destination = os.environ.get("PFP_PILOT_000016_MUTATION_OUTPUT")
    if destination:
        with Path(destination).open("x",encoding="utf-8",newline="\n") as stream:
            json.dump(rows,stream,indent=2)
    assert len(rows) == len(MUTATIONS) == 21


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(RUNNER), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert m.OUTPUT_ROOT == RUNNER.resolve().parent.parent / "pilot_output" / m.PILOT_ID


def test_fact_subset_comparison_is_exact():
    assert m.holds({"a": {"b": 1}}, {"a": {"b": 1, "c": 2}, "d": 3})
    assert not m.holds({"a": {"b": 1}}, {"a": 1})
    assert not m.holds({"a": 1}, {})
    assert not m.holds({"a": True}, {"a": 1})


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    report = m.exercise_report()
    assert m.demonstration_status(report) == "DEMONSTRATED"
    monkeypatch.setitem(m.SOURCE_FACTS, "DRILL8.4", {"data": {"observables": {"toy_drag": "0/1"}}})
    mismatched = m.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["DRILL8.4"]
    assert m.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
