"""Exact independent cochain/dual oracles, contract attacks, CLI and mutations."""
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
RUNNER = Path(os.environ.get("PFP_PILOT_000015_UNDER_TEST", PILOT / "run.py"))
spec = importlib.util.spec_from_file_location("quiz06_under_test", RUNNER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def task(vertices, edges, faces, name="test1"):
    return {"task_id": name, "vertices": list(vertices), "edges": [list(e) for e in edges],
            "faces": [list(f) for f in faces]}


def tri(filled=True):
    return task("abc", ["ab", "ac", "bc"], ["abc"] if filled else [])


def sphere():
    return task("abcd", combinations("abcd", 2), ["bcd", "adc", "abd", "acb"])


def bipyramid():
    vertices = ["u", "w", "n0", "n1", "n2", "n3"]
    faces = [[apex, f"n{i}", f"n{(i+1)%4}"] if apex == "u" else
             [apex, f"n{(i+1)%4}", f"n{i}"] for apex in ("u", "w") for i in range(4)]
    edges = sorted({tuple(sorted(e)) for f in faces for e in combinations(f, 2)})
    return task(vertices, edges, faces)


def double_sphere(shared):
    first = sphere()
    other = {v: "a" if shared and v == "a" else "x"+v for v in "abcd"}
    vertices = first["vertices"] + [v for v in other.values() if v not in first["vertices"]]
    return task(vertices, first["edges"] + [[other[v] for v in e] for e in first["edges"]],
                first["faces"] + [[other[v] for v in f] for f in first["faces"]])


def nodes(i, j):
    return f"v{i%3}{j%3}"


def torus():
    vertices, edges, faces, h, v = [], [], [], [], []
    for i, j in product(range(3), repeat=2):
        a, b, c, d = nodes(i,j), nodes(i+1,j), nodes(i+1,j+1), nodes(i,j+1)
        vertices.append(a)
        edges += [[a,b],[a,d],[a,c]]
        faces += [[a,b,c],[a,c,d]]
        h += [1,0,1]
        v += [0,1,1]
    return task(vertices, edges, faces), h, v


def query(kind, **kwargs):
    return {"case_id": "test1", "kind": kind, **kwargs}


def adapter(weights=None):
    return {"scheme": "positive_diagonal_edge_v1",
            "edge_weights": weights or ["1/2","2/1","3/1","4/1","5/1","6/1"]}


def qt(value):
    value = Q(value)
    return f"{value.numerator}/{value.denominator}"


def independent_d1(t):
    result = []
    for face in t["faces"]:
        row = []
        for a,b in t["edges"]:
            cycle = list(zip(face, face[1:]+face[:1], strict=True))
            row.append(int((a,b) in cycle) - int((b,a) in cycle))
        result.append(row)
    return result


def assert_dual(t, dual):
    assert dual["status"] == "CONSTRUCTED"
    assert (len(dual["vertices"]),len(dual["edges"]),len(dual["faces"])) == (len(t["faces"]),len(t["edges"]),len(t["vertices"]))
    expected1 = independent_d1(t)
    expected2 = [[int(v==a)-int(v==b) for v in t["vertices"]] for a,b in t["edges"]]
    assert dual["boundary1"] == {"rows":len(t["faces"]),"cols":len(t["edges"]),"values":expected1}
    assert dual["boundary2"] == {"rows":len(t["edges"]),"cols":len(t["vertices"]),"values":expected2}
    assert dual["boundary_product"]["values"] == [[0]*len(t["vertices"]) for _ in t["faces"]]
    assert dual["vertices"] == [{"primal_face":i} for i in range(len(t["faces"]))]
    for e,row in enumerate(dual["edges"]):
        assert row == {"primal_edge":e,"tail_face":next(i for i,r in enumerate(expected1) if r[e]==-1),
                       "head_face":next(i for i,r in enumerate(expected1) if r[e]==1)}
    for v,face in enumerate(dual["faces"]):
        assert face["primal_vertex"] == t["vertices"][v]
        steps = face["boundary_cycle"]
        assert {s["edge"] for s in steps} == {e for e,row in enumerate(expected2) if row[v]}
        assert len(steps) == len({s["edge"] for s in steps}) == len({s["from"] for s in steps})
        for index,step in enumerate(steps):
            assert step["to"] == steps[(index+1)%len(steps)]["from"]
            assert step["sign"] == expected2[step["edge"]][v]
            edge = dual["edges"][step["edge"]]
            endpoints = (edge["tail_face"],edge["head_face"])
            assert (step["from"],step["to"]) == (endpoints if step["sign"]==1 else endpoints[::-1])


def test_closure_oracle():
    edge_choices, face_choices = list(combinations("abcd",2)), list(combinations("abcd",3))
    accepted, by_faces = 0, [0]*5
    for edge_mask,face_mask in product(range(64),range(16)):
        edges = [e for i,e in enumerate(edge_choices) if edge_mask & (1<<i)]
        faces = [f for i,f in enumerate(face_choices) if face_mask & (1<<i)]
        valid = all(set(combinations(f,2)) <= set(edges) for f in faces)
        t = task("abcd",edges,faces)
        if valid:
            actual = m.complex_data(t)
            assert actual["nilpotent"]
            assert actual["d1"]["values"] == independent_d1(t)
            assert actual["d1"]["rows"]==len(faces) and actual["d1"]["cols"]==len(edges)
            accepted += 1
            by_faces[len(faces)] += 1
        else:
            with pytest.raises(m.InvalidInput):
                m.complex_data(t)
    assert accepted == 113 and by_faces == [64,32,12,4,1]


def test_orientations_and_gradients():
    count = 0
    for edge_signs,face_sign in product(product((-1,1),repeat=3),(-1,1)):
        edges = [list(e)[::s] for e,s in zip(["ab","ac","bc"],edge_signs,strict=True)]
        t = task("abc",edges,[list("abc")[::face_sign]])
        actual = m.complex_data(t)
        expected = [[int(v==b)-int(v==a) for v in "abc"] for a,b in edges]
        assert actual["d0"]["values"] == expected
        assert actual["d1"]["values"] == independent_d1(t)
        assert actual["d1d0"]["values"] == [[0,0,0]]
        for potential in product((-1,0,1),repeat=3):
            lookup = dict(zip("abc",potential,strict=True))
            wanted = [lookup[b]-lookup[a] for a,b in edges]
            assert m.answer_for(t,query("d0",cochain=list(potential)))["value"] == wanted
            assert m.classify(t,wanted)["exact"]
            assert m.classify(t,wanted)["coboundary"] == [0]
            count += 1
    assert count == 432


def test_closed_versus_exact_grid():
    counts = {}
    for filled in (False,True):
        t = tri(filled)
        closed = exact = 0
        for c in product((-1,0,1),repeat=3):
            result = m.classify(t,list(c))
            circulation = c[0]-c[1]+c[2]
            assert result["closed"] == (not filled or circulation==0)
            assert result["exact"] == (circulation==0)
            assert result["cohomology_obstruction"] == (not filled and circulation!=0)
            if result["exact"]:
                p = result["potential"]
                assert [p[1]-p[0],p[2]-p[0],p[2]-p[1]] == list(c)
                assert result["cycle_witness"] is None
            else:
                z = result["cycle_witness"]["coefficients"]
                assert [-z[0]-z[1],z[0]-z[2],z[1]+z[2]] == [0,0,0]
                assert result["cycle_witness"]["boundary"] == [0,0,0]
                assert sum(x*y for x,y in zip(z,c,strict=True)) == result["cycle_witness"]["circulation"] != 0
            closed += result["closed"]
            exact += result["exact"]
        counts[filled] = closed,exact
    assert counts == {False:(27,7),True:(7,7)}
    assert m.complex_data(tri(False))["d1"] == {"rows":0,"cols":3,"values":[]}


def test_disconnected_potentials_and_empty_shapes():
    t = task("abcd",["ab","cd"],[])
    for p in product((-1,0,1),repeat=4):
        c = [p[1]-p[0],p[3]-p[2]]
        result = m.classify(t,c)
        assert result["exact"] and result["closed"]
        assert result["potential"] == [0,c[0],0,c[1]]
    for vertices in ("","a","abc"):
        empty = task(vertices,[],[])
        result = m.complex_data(empty)
        assert result["d0"] == {"rows":0,"cols":len(vertices),"values":[]}
        assert result["d1d0"] == {"rows":0,"cols":len(vertices),"values":[]}
        assert m.classify(empty,[])["potential"] == [0]*len(vertices)
        assert m.dual_complex(empty)["status"]=="REFUSED"
    combined = task("abcdef",["ab","ac","bc","de","df","ef"],["def"])
    result = m.classify(combined,[1,0,0,0,0,0])
    assert result["classification"]=="CLOSED_NOT_EXACT" and result["coboundary"]==[0]


def test_dual_surfaces_and_torus_periods():
    for t in (sphere(),bipyramid(),double_sphere(False)):
        assert_dual(t,m.dual_complex(t))
    octa = m.dual_complex(bipyramid())
    assert [len(f["boundary_cycle"]) for f in octa["faces"]] == [4]*6
    t,h,v = torus()
    assert (len(t["vertices"]),len(t["edges"]),len(t["faces"]))==(9,27,18)
    assert_dual(t,m.dual_complex(t))
    for a,b in product((-1,0,1),repeat=2):
        c = [a*x+b*y for x,y in zip(h,v,strict=True)]
        result = m.classify(t,c)
        assert result["closed"] and result["exact"] == (a==b==0)
        horizontal = [i for i,(u,w) in enumerate(t["edges"]) if u[2]=="0" and w[2]=="0"]
        vertical = [i for i,(u,w) in enumerate(t["edges"]) if u[1]=="0" and w[1]=="0"]
        assert sum(c[i] for i in horizontal)==3*a and sum(c[i] for i in vertical)==3*b


def test_surface_refusals():
    pinched = double_sphere(True)
    isolated = sphere()
    isolated["vertices"].append("z")
    missing = sphere()
    missing["faces"].pop()
    reversed_face = sphere()
    reversed_face["faces"][0].reverse()
    excess = sphere()
    excess["vertices"].append("z")
    excess["edges"] += [["a","z"],["b","z"]]
    excess["faces"].append(["a","b","z"])
    for t in (pinched,isolated,missing,reversed_face,excess,tri(),tri(False)):
        assert m.complex_data(t)["nilpotent"]
        result = m.dual_complex(t)
        assert result["status"]=="REFUSED" and result["refusal"]=="ref<4>"
        assert m.hodge(t,[0]*len(t["edges"]),adapter(["1/1"]*len(t["edges"])))["status"]=="REFUSED"
    assert m.dual_complex(pinched)["bad_edges"] == []
    assert m.dual_complex(reversed_face)["bad_edges"]


def test_weight_grid():
    t = sphere()
    count = 0
    for weights in product(("1/2","1/1","2/1"),repeat=6):
        for index in range(6):
            c = [int(i==index) for i in range(6)]
            report = m.hodge(t,c,adapter(list(weights)))
            expected = ["0/1"]*6
            expected[index] = weights[index]
            assert report["dual_cochain"]==expected
            assert report["weighted_self_pairing"]==weights[index]
            assert report["inverse_recovery"]==[qt(v) for v in c]
            count += 1
    assert count==4374


def test_hodge_nonclosure_and_orientation():
    t = sphere()
    weights = ["2/3","3/2","5/4","7/3","11/2","13/5"]
    c = [1,-2,3,-4,5,-6]
    report = m.hodge(t,c,adapter(weights))
    assert report["dual_cochain"] == ["2/3","-3/1","15/4","-28/3","55/2","-78/5"]
    assert report["weighted_self_pairing"]=="5727/20" and report["scalar_extension"]=="Z_TO_Q"
    assert report["continuum_bridge"]=="NOT_SUPPLIED"
    assert report["metric_origin"]=="DECLARED_POSITIVE_RATIONAL_WEIGHTS_NOT_DERIVED_GEOMETRY"
    zero = m.hodge(t,[0]*6,adapter())
    assert zero["weighted_self_pairing"]=="0/1"
    exact = m.hodge(t,[-1,-1,-1,0,0,0],adapter())
    assert exact["primal_coboundary"]==[0]*4
    assert exact["dual_coboundary"]==["-11/2","1/2","2/1","3/1"]
    assert exact["weighted_self_pairing"]=="11/2"
    t["edges"][2].reverse()
    c[2] *= -1
    changed = m.hodge(t,c,adapter(weights))
    assert changed["weighted_self_pairing"]==report["weighted_self_pairing"]
    assert changed["dual_cochain"][2]=="-15/4"
    assert_dual(t,changed["dual_complex"])
    # Reindex all edges and their data; labels do not replace this basis transport.
    t["edges"].reverse()
    c.reverse()
    permuted = m.hodge(t,c,adapter(list(reversed(weights))))
    assert permuted["dual_cochain"]==list(reversed(changed["dual_cochain"]))
    assert_dual(t,permuted["dual_complex"])
    assert m.hodge(t,c,None)["reason"]=="FINITE_METRIC_ADAPTER_MISSING"


@pytest.mark.parametrize("change", [
    lambda t:t.update(vertices=["a","a","c"]),
    lambda t:t.update(vertices=["a","b"]),
    lambda t:t.update(vertices=tuple(t["vertices"])),
    lambda t:t.update(vertices=["a"]*25),
    lambda t:t.update(edges=[["a","a"]]),
    lambda t:t.update(edges=[["a"]]),
    lambda t:t.update(edges=t["edges"]+[["b","a"]]),
    lambda t:t.update(faces=t["faces"]+[["b","c","a"]]),
    lambda t:t.update(faces=[["a","b","b"]]),
    lambda t:t.update(faces=[["a","b","z"]]),
    lambda t:t.update(faces=[["a","b"]]),
    lambda t:t.update(edges=[["a","c"],["b","c"]]),
    lambda t:t.update(task_id=True),
    lambda t:t.update(vertices=["a","b",False]),
    lambda t:t.update(extra=1),
])
def test_bad_complex(change):
    t = tri()
    change(t)
    with pytest.raises(m.InvalidInput):
        m.complex_data(t)


@pytest.mark.parametrize("value", ["0/0","2/4","-0/1","01/1","1/-2","1/01","1.0"," 1/2","1","1000001/1","1/1000001",True,0,1.0,None])
def test_bad_rationals(value):
    with pytest.raises(m.InvalidInput):
        m.rational(value)


@pytest.mark.parametrize("bad", [None,[],[1,2], [1,True,0],[1,0.0,0],[1,1000001,0],["1",0,0],(1,2,3)])
def test_bad_vectors(bad):
    with pytest.raises(m.InvalidInput):
        m.classify(tri(),bad)


@pytest.mark.parametrize("weights", [[],["1/1"]*5,["1/1"]*7,["0/1"]*6,["-1/1"]*6,[True]*6,{"a":"1/1"}])
def test_bad_weights(weights):
    with pytest.raises(m.InvalidInput):
        m.hodge(sphere(),[1]*6,{"scheme":"positive_diagonal_edge_v1","edge_weights":weights})


def test_bad_adapter_and_matrices():
    for bad in ({},{"scheme":"smooth","edge_weights":["1/1"]*6},True,{"scheme":"positive_diagonal_edge_v1","edge_weights":["1/1"]*6,"bridge":True}):
        with pytest.raises(m.InvalidInput):
            m.hodge(sphere(),[0]*6,bad)
    for rows,cols,data in [(True,0,[]),(0,-1,[]),(97,0,[]),(1,2,[[1]]),(0,0,[[]]),(2,0,[[],[1]]),(1,1,[[True]])]:
        with pytest.raises(m.InvalidInput):
            m.matrix(rows,cols,data)
    assert m.transpose(m.matrix(0,3,[]))=={"rows":3,"cols":0,"values":[[],[],[]]}
    with pytest.raises(m.InvalidInput):
        m.mm(m.matrix(0,3,[]),m.matrix(0,0,[]))
    with pytest.raises(m.InvalidInput):
        m.mv(m.matrix(0,3,[]),[])


def test_source_rows_and_queries():
    report = m.exercise_report()
    rows = {r["id"]:r for r in report["exercises"]}
    assert len(rows)==len(report["exercises"])==10
    assert set(rows)=={"P6.1","P6.2A","P6.2B","P6.3","P6.4"}|{f"DRILL6.{i}" for i in range(1,6)}
    assert len(report["source_vocabulary"])==7
    assert report["source_notation"]=="HISTORICAL_LABELS_NOT_A_GENERAL_WIRE_PARSER"
    for name,row in rows.items():
        assert row["query"]["case_id"]==name
        document = m.submission(row["task"],row["query"],row["computed_answer"])
        assert m.evaluate(document)["verdict"]=="MATCH"
    assert rows["P6.1"]["computed_answer"]["d1d0"]["values"]==[[0,0,0]]
    assert rows["P6.2A"]["computed_answer"]["potential"]==[0,2,5]
    assert rows["P6.2A"]["computed_answer"]["classification"]=="EXACT"
    assert rows["P6.2B"]["computed_answer"]["coboundary"]==[1]
    assert rows["P6.3"]["computed_answer"]["dual_cochain"]==["1/2"]+["0/1"]*5
    assert rows["DRILL6.2"]["computed_answer"]["value"]==[2,5,3]
    assert rows["DRILL6.3"]["computed_answer"]["value"]==[1]
    assert rows["DRILL6.4"]["computed_answer"]["coboundary"]==[-1]
    for key in ("P6.4","DRILL6.5"):
        assert rows[key]["computed_answer"]["refusal"]=="ref<4>"
    controls=report["controls"]
    assert controls["closed_not_exact"]["classification"]=="CLOSED_NOT_EXACT"
    assert controls["incoherent_surface"]["status"]=="REFUSED"
    assert controls["forged_exact"]["verdict"]=="MISMATCH"
    assert controls["exact_primal_nonclosed_dual"]["dual_coboundary"]==["-11/2","1/2","2/1","3/1"]


def test_bad_queries_and_proposal_integrity():
    for bad in (None,[],{},{"kind":[]},{"case_id":"x","kind":"unknown"},query("import",claim="anything"),
                query("nilpotency",bridge=True),{"case_id":False,"kind":"nilpotency"}):
        with pytest.raises(m.InvalidInput):
            m.answer_for(tri(),bad)
    q=query("classify",cochain=[1,0,0])
    good=m.submission(tri(),q,m.classify(tri(),[1,0,0]))
    original=deepcopy(good)
    actual=m.evaluate(good)
    assert actual["verdict"]=="MATCH" and good==original
    assert actual["authority_effect"]==actual["genesis_effect"]=="None"
    actual["original"]["task"]["vertices"].append("z")
    assert good==original
    for path,value in [(["task","task_id"],"other"),(["task","vertices"],["c","b","a"]),
                       (["task","edges"],[["b","a"],["a","c"],["b","c"]]),(["task","faces"],[]),
                       (["query","case_id"],"other"),(["query","cochain"],[0,0,0]),(["query","kind"],"d1")]:
        changed=deepcopy(good)
        changed[path[0]][path[1]]=value
        with pytest.raises(m.InvalidInput,match="another task/query"):
            m.evaluate(changed)
    hq=query("hodge",cochain=[1]*6,adapter=adapter())
    bound=m.submission(sphere(),hq,m.hodge(sphere(),[1]*6,adapter()))
    bound["query"]["adapter"]["edge_weights"][0]="2/1"
    with pytest.raises(m.InvalidInput,match="another task/query"):
        m.evaluate(bound)
    bad=deepcopy(good)
    bad["proposal"]["answer"]["exact"]=True
    assert m.evaluate(bad)["verdict"]=="MISMATCH"
    bad=deepcopy(good)
    bad["proposal"]["answer"]["coboundary"]=[True]
    assert m.evaluate(bad)["verdict"]=="MISMATCH"
    for bad in ({},[],{**good,"unexpected":1},{**good,"proposal":{}},
                {**good,"proposal":{"problem_sha256":good["proposal"]["problem_sha256"],"answer":[]}}):
        with pytest.raises(m.InvalidInput):
            m.evaluate(bad)
    # Large but admitted input differences must remain valid structured answers.
    t=tri()
    q=query("d0",cochain=[-1000000,1000000,0])
    assert m.evaluate(m.submission(t,q,m.answer_for(t,q)))["verdict"]=="MATCH"


@pytest.mark.parametrize("raw", [b"",b"{",b'{"a":1,"a":2}',b"NaN",b"Infinity",b"-Infinity",b"\xff",b" "*131073],
                         ids=["empty","syntax","duplicate","nan","inf","minus_inf","utf8","oversize"])
def test_decode_rejected(raw):
    with pytest.raises((ValueError,UnicodeError)):
        m.decode(raw)


@pytest.mark.parametrize("value", [1.0,Q(1),{"a":object()},[1]*257,{str(i):0 for i in range(65)},
                                   {1:0},"x"*2049,"\n","\u00e9",10**19])
def test_bad_json_values(value):
    with pytest.raises(m.InvalidInput):
        m.json_value(value)


def test_depth_byte_bounds_and_helpers():
    value=0
    for _ in range(18):
        value=[value]
    with pytest.raises(m.InvalidInput):
        m.json_value(value)
    with pytest.raises(m.InvalidInput):
        m.decode("not bytes")
    m.json_value({"string":"ok","int":1,"bool":True,"null":None})
    assert m.rational("-2/3")==Q(-2,3)
    assert m.decode(b'{"b":2,"a":1}')=={"a":1,"b":2}
    big=m.submission(tri(),query("nilpotency"),{"values":["x"*2048]*65})
    with pytest.raises(m.InvalidInput,match="byte limit"):
        m.evaluate(big)


def verify_run(folder,raw=None):
    receipt=json.loads((folder/"receipt.json").read_text())
    assert receipt["code_sha256"]==hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert receipt["model_calls"]==0 and receipt["cost_usd"]=="0"
    assert set(receipt["artifact_sha256"])=={"input.bin","result.json","summary.md"}
    for name,value in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==value
    if raw is not None:
        assert (folder/"input.bin").read_bytes()==raw
    return receipt,json.loads((folder/"result.json").read_text())


def test_inprocess_cli(tmp_path,capsys):
    outputs=[]
    for _ in range(2):
        assert m.main(["--output-dir",str(tmp_path/"runs")])==0
        outputs.append(Path(json.loads(capsys.readouterr().out)["output"]))
        receipt,result=verify_run(outputs[-1])
        assert receipt["status"]=="DEMONSTRATED" and result==m.exercise_report()
    assert outputs[0]!=outputs[1]
    before={p.name:p.read_bytes() for p in outputs[0].iterdir()}
    source=tmp_path/"input.json"
    t,q=tri(),query("d1",cochain=[1,0,0])
    for document,wanted in [({},1),(m.submission(t,q,{"forged":True}),1),
                            (m.submission(t,q,m.answer_for(t,q)),0)]:
        raw=json.dumps(document,indent=2).encode()
        source.write_bytes(raw)
        assert m.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")])==wanted
        verify_run(Path(json.loads(capsys.readouterr().out)["output"]),raw)
    for raw in (b"NaN",b"x"*131073):
        source.write_bytes(raw)
        assert m.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")])==2
        assert json.loads(capsys.readouterr().out)["status"]=="REFUSED"
    assert m.main(["--input",str(tmp_path/"absent")])==2
    capsys.readouterr()
    occupied=tmp_path/"occupied"
    occupied.write_text("keep")
    assert m.main(["--output-dir",str(occupied)])==2
    capsys.readouterr()
    assert occupied.read_text()=="keep"
    assert {p.name:p.read_bytes() for p in outputs[0].iterdir()}==before


@pytest.mark.parametrize("kind",["nilpotency","d0","d1","classify","hodge","import"])
def test_real_cli(tmp_path,kind):
    t=sphere()
    kwargs={"cochain":[1]*4} if kind=="d0" else {"cochain":[1]*6} if kind in ("d1","classify","hodge") else {}
    if kind=="hodge":
        kwargs["adapter"]=adapter()
    if kind=="import":
        kwargs["claim"]="riemannian_manifold"
    q=query(kind,**kwargs)
    document=m.submission(t,q,m.answer_for(t,q))
    raw=json.dumps(document,indent=1).encode()
    source=tmp_path/"input.json"
    source.write_bytes(raw)
    result=subprocess.run([sys.executable,str(RUNNER),"--input",str(source),"--output-dir",str(tmp_path/"runs")],
                          capture_output=True,text=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    receipt,report=verify_run(Path(json.loads(result.stdout)["output"]),raw)
    assert receipt["status"]=="MATCH" and report["computed_answer"]==document["proposal"]["answer"]


MUTATIONS=[
    ("zero_d0","int(v == b) - int(v == a)","0","test_orientations_and_gradients"),
    ("lose_face_sign",'row[j] = 1 if edges[j] == [u, v] else -1',"row[j] = 1","test_orientations_and_gradients"),
    ("skip_missing_boundary",'require(key in index, "Declared face is missing a boundary edge")',
     "if key not in index:\n                continue","test_closure_oracle"),
    ("lose_empty_shape","d1 = matrix(len(faces), len(edges), rows)","d1 = matrix(len(faces), len(edges) if faces else 0, rows)","test_closed_versus_exact_grid"),
    ("closed_is_exact","closed, exact = not any(coboundary), cycle is None","closed, exact = not any(coboundary), not any(coboundary)","test_closed_versus_exact_grid"),
    ("nonclosed_as_cohomology",'"cohomology_obstruction": closed and not exact','"cohomology_obstruction": not exact',"test_closed_versus_exact_grid"),
    ("ignore_potential_sign","potentials[current] + sign * values[edge]","potentials[current] + values[edge]","test_orientations_and_gradients"),
    ("only_first_component",'for root in task["vertices"]:','for root in task["vertices"][:1]:',"test_disconnected_potentials_and_empty_shapes"),
    ("zero_cycle","x-y+int(j == i)","0","test_closed_versus_exact_grid"),
    ("skip_link_admission",'not all(row["connected_cycle"] for row in links)',"False","test_surface_refusals"),
    ("omit_dual_sign","[[-value for value in row] for row in d0[\"values\"]]","[[value for value in row] for row in d0[\"values\"]]","test_dual_surfaces_and_torus_periods"),
    ("dual_identity_vertices",'range(len(task["faces"]))','range(len(task["vertices"]))',"test_dual_surfaces_and_torus_periods"),
    ("identity_hodge","weight*value for weight, value","value for weight, value","test_hodge_nonclosure_and_orientation"),
    ("inverse_as_star","weight*value for weight, value","value/weight for weight, value","test_hodge_nonclosure_and_orientation"),
    ("truncate_star","weight*value for weight, value","int(weight*value) for weight, value","test_hodge_nonclosure_and_orientation"),
    ("ignore_positive_weights","require(all(value > 0 for value in weights),","require(True,","test_bad_weights"),
    ("inverse_wrong","value/weight for value, weight","value*weight for value, weight","test_weight_grid"),
    ("wrong_pairing","v*w for v, w","w*w for v, w","test_hodge_nonclosure_and_orientation"),
    ("claim_dual_closed",'"dual_coboundary": [qtext(value) for value in dual_coboundary]','"dual_coboundary": ["0/1"] * len(dual_coboundary)',"test_hodge_nonclosure_and_orientation"),
    ("continuum_promotion",'return {"refusal": "ref<4>", "claim":','return {"refusal": None, "claim":',"test_source_rows_and_queries"),
    ("drop_problem_binding",'require(snapshot["proposal"]["problem_sha256"] == problem,',"require(True,","test_bad_queries_and_proposal_integrity"),
    ("always_match",'matches = encoded(snapshot["proposal"]["answer"]) == encoded(computed)',"matches = True","test_bad_queries_and_proposal_integrity"),
    ("duplicate_json","require(key not in result,","require(True,","test_decode_rejected"),
    ("noncanonical_rational","require(qtext(parsed) == value,","require(True,","test_bad_rationals"),
]


def test_implementation_mutations(tmp_path):
    if os.environ.get("PFP_PILOT_000015_UNDER_TEST"):
        return
    original_raw=RUNNER.read_bytes()
    source=RUNNER.read_text(encoding="utf-8")
    rows=[]
    for name,anchor,replacement,selection in MUTATIONS:
        assert source.count(anchor)==1,(name,source.count(anchor))
        assert anchor!=replacement
        mutant=source.replace(anchor,replacement)
        compile(mutant,name,"exec")
        target=tmp_path/(name+".py")
        target.write_text(mutant,encoding="utf-8",newline="\n")
        xml=tmp_path/(name+".xml")
        env=dict(os.environ,PFP_PILOT_000015_UNDER_TEST=str(target),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONDONTWRITEBYTECODE="1")
        child=subprocess.run([sys.executable,"-m","pytest",str(Path(__file__).resolve()),"-q","-p","no:cacheprovider","-o","addopts=",
                              "--import-mode=importlib","--basetemp",str(tmp_path/(name+"_tmp")),"--junitxml",str(xml),"-k",selection],
                             capture_output=True,text=True,env=env,check=False)
        failures=[case.attrib["name"] for case in ET.parse(xml).iter("testcase") if case.find("failure") is not None]
        assert child.returncode==1 and failures,(name,child.stdout,child.stderr)
        assert RUNNER.read_bytes()==original_raw
        rows.append({"name":name,"target":"run.py","anchor":anchor,"replacement":replacement,"selection":selection,
                     "applied":True,"exit_code":child.returncode,"failed_nodes":failures,"original_unchanged":True,
                     "original_sha256":hashlib.sha256(original_raw).hexdigest(),"mutant_sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    destination=os.environ.get("PFP_PILOT_000015_MUTATION_OUTPUT")
    if destination:
        with Path(destination).open("x",encoding="utf-8",newline="\n") as stream:
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
    monkeypatch.setitem(m.SOURCE_FACTS, "DRILL6.2", {"value": [2, 5, 4]})
    mismatched = m.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["DRILL6.2"]
    assert m.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
