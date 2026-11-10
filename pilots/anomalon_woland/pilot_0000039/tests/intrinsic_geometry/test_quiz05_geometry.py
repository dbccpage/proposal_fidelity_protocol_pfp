"""Independent finite geometry oracles, contract attacks, real CLI and mutations."""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
from itertools import combinations, product
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

PILOT = Path(__file__).resolve().parents[2]
RUNNER = Path(os.environ.get("PFP_PILOT_000014_UNDER_TEST", PILOT / "run.py"))
spec = importlib.util.spec_from_file_location("quiz05_under_test", RUNNER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def qt(value):
    value = Q(value)
    return f"{value.numerator}/{value.denominator}"


def tri_task(x=1, y=1, z=1, area=None):
    return {"task_id": "triangle1", "vertices": ["a", "b", "c"],
            "edges": [{"vertices": ["a", "b"], "length_squared": qt(x)},
                      {"vertices": ["a", "c"], "length_squared": qt(y)},
                      {"vertices": ["b", "c"], "length_squared": qt(z)}],
            "faces": [{"vertices": ["a", "b", "c"], "area_squared": None if area is None else qt(area)}]}


def graph_task(size, pairs):
    neighbors = [f"n{i}" for i in range(size)]
    edges = [["v", n] for n in neighbors] + [[neighbors[a], neighbors[b]] for a, b in pairs]
    return {"task_id": "graph1", "vertices": ["v", *neighbors],
            "edges": [{"vertices": e, "length_squared": "1/1"} for e in edges],
            "faces": [{"vertices": ["v", neighbors[a], neighbors[b]], "area_squared": None} for a, b in pairs]}


def bipyramid():
    faces = [[apex, f"n{i}", f"n{(i+1)%6}"] for apex in ("u", "w") for i in range(6)]
    edges = sorted({tuple(sorted(pair)) for face in faces for pair in combinations(face, 2)})
    return {"task_id": "bipyramid1", "vertices": ["u", "w"] + [f"n{i}" for i in range(6)],
            "edges": [{"vertices": list(e), "length_squared": "1/1"} for e in edges],
            "faces": [{"vertices": f, "area_squared": None} for f in faces]}


def test_triangle_grid():
    counts = {"positive": 0, "degenerate": 0, "invalid": 0}
    elementary = 0
    for x, y, z in product(map(Q, (1, 2, 3, 4, 5, 7, 9)), repeat=3):
        delta = 2*x*y + 2*x*z + 2*y*z - x*x - y*y - z*z
        result = m.triangle(x, y, z)
        if delta > 0:
            counts["positive"] += 1
            assert result["status"] == "VALID_TRIANGLE"
            assert result["area_squared"] == qt(delta / 16)
            cosine = (x+y-z)**2/(4*x*y)
            corner = result["angles"][0]
            assert corner["cosine_squared"] == qt(cosine)
            assert corner["cosine_sign"] == (1 if x+y>z else -1 if x+y<z else 0)
            expected = {Q(0): Q(1,2), Q(1,4): Q(1,3), Q(1,2): Q(1,4), Q(3,4): Q(1,6)}.get(cosine)
            if expected is not None:
                if x+y<z:
                    expected = 1-expected
                assert corner["pi_multiple"] == qt(expected)
                elementary += 1
            else:
                assert corner["pi_multiple"] is None
        else:
            counts["degenerate" if delta == 0 else "invalid"] += 1
            assert result == {"status": "DEGENERATE" if delta == 0 else "INVALID_TRIANGLE", "area_squared": None, "angles": None}
    assert counts == {"positive": 304, "degenerate": 9, "invalid": 30}
    assert elementary == 51


def squared(u, v):
    return Q(sum((x-y)**2 for x,y in zip(u, v, strict=True)))


def test_coordinate_oracle():
    count = 0
    for s, t, h in product((1,2,3), (-1,0,1,2), (-2,-1,1,2)):
        a, b, c = (0,0), (s,0), (t,h)
        result = m.geometry(tri_task(squared(a,b), squared(a,c), squared(b,c)))
        assert result["status"] == "COMPLETE_METRIC_COMPLEX"
        assert result["triangles"][0]["area_squared"] == qt(Q((s*h)**2,4))
        count += 1
    assert count == 48
    assert m.geometry(tri_task())["triangles"][0]["area_squared"] == "3/16"


def test_closure_oracle():
    vertices = ["a","b","c","d"]
    edges, faces = list(combinations(vertices,2)), list(combinations(vertices,3))
    closed_count = 0
    for edge_mask, face_mask in product(range(64), range(16)):
        selected_edges = {e for i,e in enumerate(edges) if edge_mask & (1<<i)}
        selected_faces = [f for i,f in enumerate(faces) if face_mask & (1<<i)]
        task = {"task_id":"closure1","vertices":vertices,
                "edges":[{"vertices":list(e),"length_squared":"1/1"} for e in selected_edges],
                "faces":[{"vertices":list(f),"area_squared":None} for f in selected_faces]}
        needed = {e for f in selected_faces for e in combinations(f,2)}
        closed = needed <= selected_edges
        assert (m.geometry(task)["status"] == "COMPLETE_METRIC_COMPLEX") is closed
        closed_count += closed
    assert closed_count == 113


def test_link_graph_oracle():
    counts = {"INTERIOR_CYCLE":0, "BOUNDARY_PATH":0, "NON_SURFACE":0}
    total = 0
    for size in range(6):
        all_pairs = list(combinations(range(size),2))
        for mask in range(1 << len(all_pairs)):
            pairs = [e for i,e in enumerate(all_pairs) if mask & (1<<i)]
            reach = {0} if size else set()
            while True:
                extended = reach | {b for a,b in pairs if a in reach} | {a for a,b in pairs if b in reach}
                if extended == reach:
                    break
                reach = extended
            degrees = [sum(v in e for e in pairs) for v in range(size)]
            kind = "NON_SURFACE"
            if size >= 3 and len(reach) == size and degrees == [2]*size:
                kind = "INTERIOR_CYCLE"
            elif size >= 2 and len(reach) == size and sorted(degrees) == [1,1]+[2]*(size-2):
                kind = "BOUNDARY_PATH"
            task = graph_task(size, pairs)
            result = m.vertex_link(*m.presentation(task), "v")
            assert result["kind"] == kind
            counts[kind] += 1
            total += 1
    assert total == 1100
    assert counts == {"INTERIOR_CYCLE":16,"BOUNDARY_PATH":76,"NON_SURFACE":1008}


@pytest.mark.parametrize("boundary,count,rim", [(b,n,r) for b in (False,True) for n in (range(1,6) if b else range(3,9)) for r in (1,2,3)])
def test_fans(boundary, count, rim):
    task = m.fan(count, qt(rim), boundary)
    result = m.vertex_defect(task,"v")
    theta = {1:Q(1,3),2:Q(1,2),3:Q(2,3)}[rim]
    expected = (1 if boundary else 2) - count*theta
    assert result["quantity"] == ("BOUNDARY_TURNING" if boundary else "INTERIOR_ANGLE_DEFECT")
    assert result["pi_multiple"] == qt(expected)
    assert result["classification"] == ("ZERO" if expected==0 else "POSITIVE" if expected>0 else "NEGATIVE")
    assert result["global_flatness"] == "NOT_INFERRED"


def test_surface_sums_and_local_global():
    for task in [m.fan(5),m.fan(6),m.fan(7),m.fan(3,boundary=True),bipyramid()]:
        defects = [m.vertex_defect(task,v) for v in task["vertices"]]
        assert all(d["classification"] != "UNDEFINED" for d in defects)
        total = sum(Q(d["pi_multiple"]) for d in defects)
        assert total == 2*(len(task["vertices"])-len(task["edges"])+len(task["faces"]))
    task = bipyramid()
    assert (len(task["vertices"]),len(task["edges"]),len(task["faces"])) == (8,18,12)
    assert m.vertex_defect(task,"u")["pi_multiple"] == "0/1"
    assert m.vertex_defect(task,"w")["pi_multiple"] == "0/1"
    assert {m.vertex_defect(task,f"n{i}")["pi_multiple"] for i in range(6)} == {"2/3"}
    assert m.answer_for(task,{"kind":"global_from_vertex","vertex":"u"})["refusal"] == "ref<2>"


def test_bad_topology():
    pairs = [(0,1),(1,2),(0,2),(3,4),(4,5),(3,5)]
    task = graph_task(6,pairs)
    result = m.vertex_defect(task,"v")
    assert result["status"] == "NON_SURFACE_VERTEX"
    assert result["link"]["connected"] is False
    assert set(result["link"]["degrees"].values()) == {2}
    assert result["classification"] == "UNDEFINED"
    task = m.fan(6)
    task["vertices"].append("dangling")
    task["edges"].append({"vertices":["v","dangling"],"length_squared":"1/1"})
    assert m.vertex_defect(task,"v")["link"]["degrees"]["dangling"] == 0
    assert m.vertex_defect(task,"v")["status"] == "NON_SURFACE_VERTEX"
    assert m.vertex_defect(graph_task(4,[(0,1),(0,2),(0,3)]),"v")["status"] == "NON_SURFACE_VERTEX"


def test_unknown_angles_not_nonzero():
    task = m.fan(4)
    for i,edge in enumerate(task["edges"][4:]):
        edge["length_squared"] = "1/2" if i%2==0 else "7/2"
    result = m.vertex_defect(task,"v")
    assert result["status"] == "EXACT_EXPRESSION_UNRESOLVED"
    assert result["classification"] == "UNKNOWN" and result["pi_multiple"] is None
    assert [a["cosine_sign"] for a in result["expression"]["subtract_angles"]].count(1) == 2
    assert {a["cosine_squared"] for a in result["expression"]["subtract_angles"]} == {"9/16"}
    assert {f["area_squared"] for f in m.geometry(task)["triangles"]} == {"7/64"}
    # acos(3/4)+acos(-3/4)=pi: a real zero outside the implemented recognizer.
    near = m.fan(6,"999999/1000000")
    assert m.vertex_defect(near,"v")["classification"] == "UNKNOWN"


def test_metric_and_order_invariance():
    original = m.fan(5,"3/1")
    transformed = deepcopy(original)
    for edge in transformed["edges"]:
        edge["length_squared"] = qt(Q(edge["length_squared"])*Q(7,3))
        edge["vertices"].reverse()
    for face in transformed["faces"]:
        face["vertices"].reverse()
    transformed["faces"].reverse()
    transformed["edges"].reverse()
    assert m.vertex_defect(original,"v") == m.vertex_defect(transformed,"v")
    before, after = m.geometry(original),m.geometry(transformed)
    assert [Q(t["area_squared"])*Q(49,9) for t in before["triangles"]] == [Q(t["area_squared"]) for t in after["triangles"]]
    rename = {v:f"x{i}" for i,v in enumerate(original["vertices"])}
    transformed["vertices"] = [rename[v] for v in transformed["vertices"]]
    for row in transformed["edges"]+transformed["faces"]:
        row["vertices"] = [rename[v] for v in row["vertices"]]
    assert m.vertex_defect(transformed,rename["v"])["pi_multiple"] == m.vertex_defect(original,"v")["pi_multiple"]


def test_partial_completion_and_binding():
    old, new = m.declaration(), m.declaration(True)
    before = deepcopy(old)
    report = m.geometry(old)
    assert report["status"] == "INCOMPLETE_DECLARATION"
    assert report["missing_vertices"] == ["b","c"]
    assert report["missing_edges"] == [["a","c"],["b","c"]]
    result = m.completion(old,new,m.digest(old))
    assert result["accepted"] is True and result["genesis_effect"] == "None"
    assert result["completion_geometry"]["triangles"][0]["area_squared"] == "4/1"
    alternate = tri_task(4,5,5,4)
    assert m.completion(old,alternate,m.digest(old))["accepted"] is True
    assert m.completion(old,new,"0"*64)["accepted"] is False
    for change in ("id","vertex","edge","area","missing_face"):
        altered = deepcopy(new)
        if change=="id":
            altered["task_id"]=old["task_id"]
        elif change=="vertex":
            altered["vertices"].remove("a")
        elif change=="edge":
            altered["edges"][0]["length_squared"]="3/1"
        elif change=="area":
            altered["faces"][0]["area_squared"]="9/1"
        else:
            altered["faces"]=[]
        assert m.completion(old,altered,m.digest(old))["accepted"] is False
    unspecified = deepcopy(old)
    unspecified["faces"][0]["area_squared"] = None
    assert m.completion(unspecified,new,m.digest(unspecified))["accepted"] is True
    changed_metric = tri_task(3,4,8)
    assert m.geometry(changed_metric)["status"] == "COMPLETE_METRIC_COMPLEX"
    assert m.completion(unspecified,changed_metric,m.digest(unspecified))["accepted"] is False
    assert m.completion(old,old,m.digest(old))["accepted"] is False
    assert old == before
    query = {"kind":"complete","completion":new,"original_sha256":m.digest(old)}
    assert m.answer_for(old,query) == result


def test_invalid_metrics_and_area():
    assert m.geometry(tri_task(1,1,4))["status"] == "INVALID_METRIC"
    assert m.geometry(tri_task(1,1,5))["invalid_faces"] == [["a","b","c"]]
    assert m.geometry(tri_task(area=1))["triangles"][0]["supplied_area_consistent"] is False
    assert m.geometry(tri_task(area=Q(3,16)))["status"] == "COMPLETE_METRIC_COMPLEX"
    with pytest.raises(m.InvalidInput):
        m.vertex_defect(m.declaration(),"a")
    with pytest.raises(m.InvalidInput):
        m.vertex_defect(tri_task(),"d")
    with pytest.raises(m.InvalidInput):
        m.angle(Q(1),Q(1),Q(4))
    with pytest.raises(m.InvalidInput):
        m.angle(Q(0),Q(1),Q(1))
    with pytest.raises(m.InvalidInput):
        m.triangle(Q(0),Q(1),Q(1))


@pytest.mark.parametrize("change", ["extra","task_id","vertex_type","vertex_max","vertex_duplicate","vertex_id",
                                   "edge_type","edge_max","face_type","face_max","edge_fields","edge_arity",
                                   "edge_repeated","edge_duplicate","length_zero","length_negative","length_bool",
                                   "face_fields","face_arity","face_repeated","face_duplicate","area_negative","area_zero"])
def test_bad_presentation(change):
    task = tri_task()
    if change=="extra":
        task["extra"]=0
    elif change=="task_id":
        task["task_id"]="NotValid"
    elif change=="vertex_type":
        task["vertices"]="abc"
    elif change=="vertex_max":
        task["vertices"]=[f"v{i}" for i in range(33)]
    elif change=="vertex_duplicate":
        task["vertices"].append("a")
    elif change=="vertex_id":
        task["vertices"][0]=True
    elif change=="edge_type":
        task["edges"]={}
    elif change=="edge_max":
        task["edges"]*=33
    elif change=="face_type":
        task["faces"]={}
    elif change=="face_max":
        task["faces"]*=65
    elif change=="edge_fields":
        task["edges"][0]["extra"]=0
    elif change=="edge_arity":
        task["edges"][0]["vertices"]=["a"]
    elif change=="edge_repeated":
        task["edges"][0]["vertices"]=["a","a"]
    elif change=="edge_duplicate":
        task["edges"].append({"vertices":["b","a"],"length_squared":"2/1"})
    elif change=="length_zero":
        task["edges"][0]["length_squared"]="0/1"
    elif change=="length_negative":
        task["edges"][0]["length_squared"]="-1/1"
    elif change=="length_bool":
        task["edges"][0]["length_squared"]=True
    elif change=="face_fields":
        task["faces"][0]["extra"]=0
    elif change=="face_arity":
        task["faces"][0]["vertices"]=["a","b"]
    elif change=="face_repeated":
        task["faces"][0]["vertices"]=["a","a","b"]
    elif change=="face_duplicate":
        task["faces"].append({"vertices":["c","a","b"],"area_squared":None})
    elif change=="area_negative":
        task["faces"][0]["area_squared"]="-3/16"
    else:
        task["faces"][0]["area_squared"]="0/1"
    with pytest.raises(m.InvalidInput):
        m.presentation(task)


@pytest.mark.parametrize("value", [True,1,1.0,"1","01/1","1/0","-0/1","2/2","1000001/1","1/1000001","0/2","1/-1"," 1/1"])
def test_rationals_rejected(value):
    with pytest.raises(m.InvalidInput):
        m.rational(value)


@pytest.mark.parametrize("value", [1.2,10**13,"x"*513,"\ud800",[None]*129,{str(i):0 for i in range(65)},{1:0},set()])
def test_json_rejected(value):
    with pytest.raises(m.InvalidInput):
        m.json_value(value)


def test_json_depth_and_valid():
    m.json_value({"a":[None,False,True,-1,"ok",{}]})
    value = 0
    for _ in range(13):
        value=[value]
    with pytest.raises(m.InvalidInput):
        m.json_value(value)
    assert m.decode(b'{"a":1}') == {"a":1}
    assert m.rational("-1/2") == Q(-1,2)


@pytest.mark.parametrize("raw", [b"",b"x",b"\xff",b'{"a":1,"a":2}',b"NaN",b"Infinity",b"-Infinity",b"x"*131073], ids=["empty","syntax","utf8","duplicate","nan","inf","neg_inf","oversized"])
def test_decode_rejected(raw):
    with pytest.raises((ValueError,m.InvalidInput)):
        m.decode(raw)


def test_queries_and_source_replay():
    report = m.exercise_report()
    rows = {row["id"]:row for row in report["exercises"]}
    assert len(rows)==len(report["exercises"])==9
    assert set(rows)=={f"P5.{i}" for i in range(1,5)}|{f"DRILL5.{i}" for i in range(1,6)}
    assert len(report["source_vocabulary"])==8
    assert rows["P5.1"]["computed_answer"]["status"]=="INCOMPLETE_DECLARATION"
    assert rows["P5.2"]["computed_answer"]["classification"]=="ZERO"
    assert rows["P5.3"]["computed_answer"]["pi_multiple"]=="1/3"
    assert rows["DRILL5.1"]["computed_answer"]["length_squared"]=="2/1"
    for name in ("DRILL5.2","DRILL5.3"):
        assert rows[name]["computed_answer"]["status"]=="SUPPLIED_LABEL_GEOMETRY_UNVERIFIED"
        assert rows[name]["computed_answer"]["curvature"]=="NOT_MEASURED"
    for name in ("P5.4","DRILL5.4","DRILL5.5"):
        assert rows[name]["computed_answer"]["refusal"]=="ref<3>"
    assert report["completion_witness"]["accepted"] is True
    assert report["controls"]["forged_flat"]["verdict"]=="MISMATCH"
    assert rows["P5.2"]["computed_answer"]["pi_multiple"]=="0/1"
    assert rows["P5.3"]["computed_answer"]["classification"]=="POSITIVE"
    stated = {"DRILL5.1": {"length_squared":"2/1","status":"VALID_EDGE_ONLY","surface_geometry":"NOT_INFERRED","vertices":["a","b"]},
              "P5.4": {"authority_effect":"None","claim":"einstein_field_equations",
                       "reason":"PHYSICAL_DERIVATION_NOT_SUPPLIED","refusal":"ref<3>"}}
    for name, answer in stated.items():
        assert m.evaluate(m.submission(rows[name]["task"],rows[name]["query"],answer))["verdict"]=="MATCH"
    assert [row["verdict"] for row in report["exercises"]]==["MATCH"]*9


@pytest.mark.parametrize("query", [[],{"kind":[]},{"kind":"unknown"},{"kind":"geometry","extra":0},
                                  {"kind":"edge","vertices":["a","d"]},{"kind":"label","hinge":["a","b"],"label":"r2"},
                                  {"kind":"physics","claim":"magic"},{"kind":"vertex","vertex":["a","b"]}])
def test_bad_queries(query):
    with pytest.raises(m.InvalidInput):
        m.answer_for(tri_task(),query)


def test_proposal_integrity():
    task, query = m.fan(6), {"kind":"vertex","vertex":"v"}
    document = m.submission(task,query,m.vertex_defect(task,"v"))
    before = deepcopy(document)
    result = m.evaluate(document)
    assert result["verdict"]=="MATCH" and document==before
    result["original"]["task"]["vertices"].append("changed")
    assert document==before
    for key in ("task","query"):
        wrong = deepcopy(document)
        if key=="task":
            wrong[key]["task_id"]="other"
        else:
            wrong[key]["vertex"]="v0"
        with pytest.raises(m.InvalidInput):
            m.evaluate(wrong)
    wrong = deepcopy(document)
    wrong["proposal"]["answer"]["pi_multiple"]="1/1"
    assert m.evaluate(wrong)["verdict"]=="MISMATCH"
    wrong["proposal"]["answer"]=True
    with pytest.raises(m.InvalidInput):
        m.evaluate(wrong)
    wrong = deepcopy(document)
    wrong["proposal"]["extra"]=None
    with pytest.raises(m.InvalidInput):
        m.evaluate(wrong)
    oversized = deepcopy(document)
    oversized["proposal"]["answer"]={"p":[["x"*512]*128]*3}
    with pytest.raises(m.InvalidInput):
        m.evaluate(oversized)


@pytest.mark.parametrize("args", [(True,), (0,), (2,), (13,), (3,"1/1",1)])
def test_fan_contract(args):
    with pytest.raises(m.InvalidInput):
        m.fan(*args)


def verify_run(folder, raw=None):
    receipt = json.loads((folder/"receipt.json").read_text())
    assert receipt["code_sha256"]==hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert receipt["model_calls"]==0 and receipt["cost_usd"]=="0"
    assert set(receipt["artifact_sha256"])=={"input.bin","result.json","summary.md"}
    for name,expected in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==expected
    if raw is not None:
        assert (folder/"input.bin").read_bytes()==raw
    return receipt,json.loads((folder/"result.json").read_text())


def test_inprocess_cli(tmp_path,capsys):
    assert m.main(["--output-dir",str(tmp_path/"out")])==0
    first = json.loads(capsys.readouterr().out)
    receipt,report = verify_run(Path(first["output"]))
    assert receipt["status"]=="DEMONSTRATED" and report==m.exercise_report()
    assert m.main(["--output-dir",str(tmp_path/"out")])==0
    second = json.loads(capsys.readouterr().out)
    assert first["output"] != second["output"]
    input_file = tmp_path/"input.json"
    for document,wanted in [({},1), (m.submission(tri_task(),{"kind":"geometry"},{"forged":True}),1)]:
        raw = json.dumps(document,indent=2).encode()
        input_file.write_bytes(raw)
        assert m.main(["--input",str(input_file),"--output-dir",str(tmp_path/"out")])==wanted
        verify_run(Path(json.loads(capsys.readouterr().out)["output"]),raw)
    input_file.write_bytes(b"NaN")
    assert m.main(["--input",str(input_file),"--output-dir",str(tmp_path/"out")])==2
    assert json.loads(capsys.readouterr().out)["status"]=="REFUSED"
    assert m.main(["--input",str(tmp_path/"absent")])==2
    capsys.readouterr()
    blocked = tmp_path/"blocked"
    blocked.write_text("occupied")
    assert m.main(["--output-dir",str(blocked)])==2
    capsys.readouterr()


@pytest.mark.parametrize("count,rim,boundary", [(5,"1/1",False),(6,"1/1",False),(7,"1/1",False),(4,"1/2",False),(3,"1/1",True)])
def test_real_cli(tmp_path,count,rim,boundary):
    task = m.fan(count,rim,boundary)
    query = {"kind":"vertex","vertex":"v"}
    document = m.submission(task,query,m.vertex_defect(task,"v"))
    raw = json.dumps(document,indent=1).encode()
    input_file = tmp_path/"input.json"
    input_file.write_bytes(raw)
    result = subprocess.run([sys.executable,str(RUNNER),"--input",str(input_file),"--output-dir",str(tmp_path/"runs")],capture_output=True,text=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    receipt,report = verify_run(Path(json.loads(result.stdout)["output"]),raw)
    assert receipt["status"]=="MATCH" and report["computed_answer"]==document["proposal"]["answer"]


MUTATIONS = [
    ("area_factor","discriminant / 16","discriminant / 4","test_coordinate_oracle"),
    ("metric_sign","if discriminant <= 0:","if discriminant >= 0:","test_triangle_grid"),
    ("obtuse_sign","multiple = 1 - multiple","multiple = multiple","test_triangle_grid"),
    ("angle_table","Fraction(1, 4): Fraction(1, 3)","Fraction(1, 4): Fraction(1, 2)","test_fans"),
    ("unknown_as_zero",'"UNKNOWN" if deficit is None','"ZERO" if deficit is None',"test_unknown_angles_not_nonzero"),
    ("negative_as_zero",'"NEGATIVE"\n    return','"ZERO"\n    return',"test_fans"),
    ("boundary_turn","else 1\n    quantity","else 2\n    quantity","test_fans"),
    ("interior_turn","turns = 2 if","turns = 1 if","test_fans"),
    ("disconnected","connected = bool(neighbors) and seen == neighbors","connected = bool(neighbors)","test_bad_topology"),
    ("drop_dangling","connected = bool(neighbors) and seen == neighbors","adjacency = {v:n for v,n in adjacency.items() if n}\n    neighbors = set(adjacency)\n    connected = bool(neighbors) and seen == neighbors","test_bad_topology"),
    ("ignore_closure","if missing_vertices or missing_edges else","if False else","test_closure_oracle"),
    ("ignore_area","supplied == Fraction(result[\"area_squared\"])","True","test_invalid_metrics_and_area"),
    ("nonpositive_length","require(length > 0,","require(length >= 0,","test_bad_presentation"),
    ("nonpositive_area","require(area is None or area > 0,","require(True,","test_bad_presentation"),
    ("duplicate_edge","require(key not in edges,","require(True,","test_bad_presentation"),
    ("duplicate_face","require(key not in faces,","require(True,","test_bad_presentation"),
    ("drop_completion_binding","accepted = bound and preserves","accepted = preserves","test_partial_completion_and_binding"),
    ("change_completion_metric","new_edges.get(e) == value","e in new_edges","test_partial_completion_and_binding"),
    ("trust_label",'"curvature": "NOT_MEASURED"','"curvature": "MEASURED"',"test_queries_and_source_replay"),
    ("physics_promotion",'return {"refusal": "ref<3>", "reason": "PHYSICAL_DERIVATION_NOT_SUPPLIED"',
     'return {"refusal": None, "reason": "PHYSICAL_DERIVATION_NOT_SUPPLIED"',"test_queries_and_source_replay"),
    ("proposal_binding","require(snapshot[\"proposal\"][\"problem_sha256\"] == problem,","require(True,","test_proposal_integrity"),
    ("answer_match","matches = encoded(snapshot[\"proposal\"][\"answer\"]) == encoded(computed)","matches = True","test_proposal_integrity"),
    ("duplicate_json","require(key not in result,","require(True,","test_decode_rejected"),
    ("rational_canonical","require(qtext(parsed) == value,","require(True,","test_rationals_rejected"),
]


def test_implementation_mutations(tmp_path):
    if os.environ.get("PFP_PILOT_000014_UNDER_TEST"):
        return
    original_raw = RUNNER.read_bytes()
    source = RUNNER.read_text(encoding="utf-8")
    rows = []
    for name,anchor,replacement,selection in MUTATIONS:
        assert source.count(anchor)==1,(name,source.count(anchor))
        assert anchor != replacement
        mutated = source.replace(anchor,replacement)
        compile(mutated,name,"exec")
        path = tmp_path/(name+".py")
        path.write_text(mutated,encoding="utf-8")
        xml = tmp_path/(name+".xml")
        env = dict(os.environ,PFP_PILOT_000014_UNDER_TEST=str(path),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONDONTWRITEBYTECODE="1")
        child = subprocess.run([sys.executable,"-m","pytest",str(Path(__file__).resolve()),"-q","-p","no:cacheprovider","-o","addopts=",
                                "--import-mode=importlib","--basetemp",str(tmp_path/(name+"_tmp")),"--junitxml",str(xml),"-k",selection],
                               capture_output=True,text=True,env=env,check=False)
        failures = [case.attrib["name"] for case in ET.parse(xml).iter("testcase") if case.find("failure") is not None]
        assert child.returncode==1 and failures,(name,child.stdout,child.stderr)
        assert RUNNER.read_bytes()==original_raw
        rows.append({"name":name,"anchor":anchor,"replacement":replacement,"selection":selection,"applied":True,"exit_code":child.returncode,
                     "failed_nodes":failures,"original_unchanged":True,"original_sha256":hashlib.sha256(original_raw).hexdigest(),
                     "mutant_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    output = os.environ.get("PFP_PILOT_000014_MUTATION_OUTPUT")
    if output:
        with Path(output).open("x",encoding="utf-8") as stream:
            json.dump(rows,stream,indent=2)
    assert len(rows)==24


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
    monkeypatch.setitem(m.SOURCE_FACTS, "P5.3", {"classification": "ZERO"})
    mismatched = m.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["P5.3"]
    assert m.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
