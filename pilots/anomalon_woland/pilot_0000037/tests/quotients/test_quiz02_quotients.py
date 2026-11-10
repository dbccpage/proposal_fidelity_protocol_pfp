from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

RUNNER = Path(os.environ.get("PFP_PILOT_000012_UNDER_TEST", Path(__file__).resolve().parents[2] / "run.py"))
spec = importlib.util.spec_from_file_location("quiz02_under_test", RUNNER)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def partitions(n):
    for labels in itertools.product(range(n), repeat=n):
        if labels[0] == 0 and all(labels[i] <= 1 + max(labels[:i]) for i in range(1, n)):
            yield labels


def finite_task(labels):
    names = [f"x{i}" for i in range(len(labels))]
    return {"task_id": "finite", "records": [{"id": name, "payload": "a"} for name in names],
            "quotient": {name: f"q{label}" for name, label in zip(names, labels, strict=True)},
            "downstream": {f"q{label}": "0" for label in labels}, "demands": [], "candidates": []}


def test_source_mapping_and_controls():
    report = p.exercise_report()
    rows = {row["id"]: row for row in report["exercises"]}
    assert len(rows) == 10
    assert set(rows) == {f"P2.{i}" for i in range(1, 5)} | {"P2.3_ENUM"} | {f"DRILL2.{i}" for i in range(1, 6)}
    assert all(row["result"]["verdict"] == "MATCH" for row in rows.values())
    assert rows["P2.4"]["result"]["computed_answer"]["delta"] == 1
    assert rows["DRILL2.5"]["result"]["computed_answer"] == {"survivors": [["a", "ab"]], "count": 1}
    assert rows["P2.2"]["source_answer"] == "ans<norecov<eq<f<q1<a>>,f<q1<ab>>>>>"
    assert {key for key, value in report["controls"].items() if value["verdict"] == "MISMATCH"} == {"forged_collision", "forged_survivor_reduction"}
    assert [row["candidate_id"] for row in report["candidate_checks"]] == ["decl", "del", "ins", "subst"]
    assert report["additional_observers"]["substitution_extended_but_opaque"]["survivors"] == [["a", "ab"]]
    assert report["additional_observers"]["insertion_with_trace"]["survivors"] == []
    assert report["additional_observers"]["substitution_with_literal_readout"]["survivors"] == []
    assert report["cost_comparison"]["minimum_ids"] == ["decl", "del"]
    assert report["cost_comparison"]["partition_classes"] == [["decl", "del"]]
    assert report["authority_effect"] == report["genesis_effect"] == "None"


def test_all_small_partitions_downstream_and_factorization():
    partition_count = downstream_count = factor_count = 0
    for n in range(1, 5):
        names = [f"x{i}" for i in range(n)]
        for labels in partitions(n):
            partition_count += 1
            task = finite_task(labels)
            classes = sorted(task["downstream"])
            for bits in itertools.product(("0", "1"), repeat=len(classes)):
                downstream_count += 1
                task["downstream"] = dict(zip(classes, bits, strict=True))
                for i, j in itertools.product(range(n), repeat=2):
                    result = p.answer_for(task, {"kind": "recovery", "left": names[i], "right": names[j]})
                    a, b = bits[classes.index(f"q{labels[i]}")], bits[classes.index(f"q{labels[j]}")]
                    assert result == {"quotient_equal": labels[i] == labels[j], "outputs": [a, b], "output_equal": a == b,
                                      "status": "NO_RECOVERY_ON_COLLAPSED_PAIR" if labels[i] == labels[j] else "NO_COLLISION_PREMISE"}
                    assert p.answer_for(task, {"kind": "collision", "left": names[i], "right": names[j]}) == {
                        "left_class": f"q{labels[i]}", "right_class": f"q{labels[j]}", "collision": labels[i] == labels[j]}
            for bits in itertools.product(("0", "1"), repeat=n):
                factor_count += 1
                values = dict(zip(names, bits, strict=True))
                expected = all(labels[i] != labels[j] or bits[i] == bits[j] for i, j in itertools.product(range(n), repeat=2))
                result = p.answer_for(task, {"kind": "factor", "values": values})
                assert result["factors"] is expected
                if expected:
                    assert result["conflict"] is None
                    assert set(result["factor"]) == set(task["quotient"].values())
                    assert all(result["factor"][task["quotient"][name]] == values[name] for name in names)
                else:
                    left, right = result["conflict"]
                    assert result["factor"] is None
                    assert task["quotient"][left] == task["quotient"][right] and values[left] != values[right]
    assert (partition_count, downstream_count, factor_count) == (23, 124, 290)


def test_all_small_refinement_pairs_and_corrupted_witnesses():
    checked = 0
    for n in range(1, 5):
        names = [f"x{i}" for i in range(n)]
        options = list(partitions(n))
        for old, new in itertools.product(options, repeat=2):
            checked += 1
            task = finite_task(old)
            new_map = {name: f"n{label}" for name, label in zip(names, new, strict=True)}
            forget = {f"n{label}": f"q{old[new.index(label)]}" for label in set(new)}
            expected = all(new[i] != new[j] or old[i] == old[j] for i, j in itertools.product(range(n), repeat=2))
            result = p.answer_for(task, {"kind": "refinement", "new_quotient": new_map, "forget": forget})
            assert result["preserves_old"] is expected
            assert result["violations"] == sorted(name for name in names if forget[new_map[name]] != task["quotient"][name])
            if expected and len(set(old)) > 1:
                for label in forget:
                    corrupt = {**forget, label: next(f"q{x}" for x in set(old) if f"q{x}" != forget[label])}
                    assert not p.answer_for(task, {"kind": "refinement", "new_quotient": new_map, "forget": corrupt})["preserves_old"]
    assert checked == 255
    task = finite_task((0, 1, 1))
    with pytest.raises(p.InvalidInput):
        p.answer_for(task, {"kind": "refinement", "new_quotient": {"x0": "n0"}, "forget": {"n0": "q0"}})
    with pytest.raises(p.InvalidInput):
        p.answer_for(task, {"kind": "refinement", "new_quotient": {"x0": "n0", "x1": "n1", "x2": "n1"}, "forget": {"n0": "missing", "n1": "q1"}})


def test_all_small_demand_subsets_against_pair_oracle():
    checked = 0
    for n in range(1, 5):
        names = [f"x{i}" for i in range(n)]
        pairs = list(itertools.combinations(range(n), 2))
        for labels in partitions(n):
            for mask in range(1 << len(pairs)):
                checked += 1
                selected = [pair for index, pair in enumerate(pairs) if mask & (1 << index)]
                task = finite_task(labels)
                task["demands"] = [[names[j], names[i]] for i, j in selected]
                expected = [[names[i], names[j]] for i, j in selected if labels[i] == labels[j]]
                assert p.answer_for(task, {"kind": "baseline"}) == {"survivors": expected, "count": len(expected)}
    assert checked == 1005


def test_four_operations_use_exact_declared_selector_and_observer():
    payloads = ["", "a", "b", "aa", "ab", "ba", "bb"]
    task = p.example_task()
    task["records"] = [{"id": f"p{i}", "payload": payload} for i, payload in enumerate(payloads)]
    task["quotient"] = {f"p{i}": "empty" if not payload else "payload" for i, payload in enumerate(payloads)}
    task["demands"] = [["p1", "p4"], ["p2", "p6"], ["p0", "p1"]]
    replacements = {"decl": "a", "del": "", "ins": "aa", "subst": ">"}
    for operation, observer in itertools.product(p.OPERATIONS, ("opaque", "literal", "selected")):
        candidate = {"id": "one", "operation": operation, "selector": ["p1"], "output_alphabet": p.ALPHABET + ">", "observer": observer, "cost": 0}
        task["candidates"] = [candidate]
        result = p.answer_for(task, {"kind": "effect", "candidate_id": "one"})
        expected = {f"p{i}": replacements[operation] if i == 1 else payload for i, payload in enumerate(payloads)}
        assert result["outputs"] == expected
        observed = {name: ("payload" if value else "empty") if observer == "opaque" else
                    value if observer == "literal" else ("selected" if name == "p1" else "other") for name, value in expected.items()}
        assert result["observations"] == observed
        expected_survivors = sorted([sorted(pair) for pair in task["demands"] if
                                     task["quotient"][pair[0]] == task["quotient"][pair[1]] and observed[pair[0]] == observed[pair[1]]])
        assert result["survivors"] == expected_survivors
        assert result["refinement"] == {"preserves_old": True, "violations": []}
        assert all(result["forget"][result["new_quotient"][name]] == old for name, old in task["quotient"].items())
        assert result["selector_factors_through_old"] is False
    task["candidates"][0]["selector"] = []
    result = p.answer_for(task, {"kind": "effect", "candidate_id": "one"})
    assert result["selector_factors_through_old"] is True
    assert result["outputs"] == {f"p{i}": payload for i, payload in enumerate(payloads)}
    assert result["survivors"] == [["p1", "p4"], ["p2", "p6"]]


def test_deletion_separation_alone_is_not_refinement():
    task = p.example_task()
    result = p.answer_for(task, {"kind": "effect", "candidate_id": "del"})
    assert result["outputs"] == {"blank": "", "a": "", "ab": "ab"}
    assert result["survivors"] == []
    assert result["raw_observer_preserves_old"] is False
    assert result["refinement"]["preserves_old"] is True
    for bits in itertools.product(("empty", "payload"), repeat=2):
        checked = p.answer_for(task, {"kind": "refinement", "new_quotient": {"blank": "empty", "a": "empty", "ab": "payload"},
                                      "forget": dict(zip(("empty", "payload"), bits, strict=True))})
        assert checked["preserves_old"] is False
    assert p.answer_for(task, {"kind": "effect", "candidate_id": "ins"})["raw_observer_preserves_old"] is True


def test_nonseparating_declaration_insertion_and_substitution():
    task = p.example_task()
    task["candidates"][0]["observer"] = "opaque"
    assert p.answer_for(task, {"kind": "effect", "candidate_id": "decl"})["survivors"] == [["a", "ab"]]
    assert p.answer_for(task, {"kind": "effect", "candidate_id": "ins"})["survivors"] == [["a", "ab"]]
    bad = p.answer_for(task, {"kind": "effect", "candidate_id": "subst"})
    assert bad["status"] == "INVALID_OUTPUT_ALPHABET" and bad["invalid_records"] == ["a"] and bad["survivors"] is None
    query = {"kind": "survivors", "candidate_id": "subst", "admission": p.admission_record(task, "subst")}
    assert p.answer_for(task, query) == {"refusal": "ref<5>", "reason": "ILL_TYPED_EXTENSION", "current": [["a", "ab"]], "current_count": 1, "applied": False}
    task["candidates"][3]["output_alphabet"] += ">"
    result = p.answer_for(task, {"kind": "effect", "candidate_id": "subst"})
    assert result["status"] == "CHECKED" and result["survivors"] == [["a", "ab"]]
    task["records"][2]["payload"] = "a"
    task["candidates"][3]["observer"] = "literal"
    assert p.answer_for(task, {"kind": "effect", "candidate_id": "subst"})["survivors"] == []
    task["candidates"][3]["selector"] = []
    assert p.answer_for(task, {"kind": "effect", "candidate_id": "subst"})["survivors"] == [["a", "ab"]]


def test_survivors_proposed_admitted_and_partial_resolution():
    task = p.example_task()
    before_bytes = p.encoded(task)
    query = {"kind": "survivors", "candidate_id": "decl", "admission": None}
    assert p.answer_for(task, query) == p.survivor_answer(False)
    query["admission"] = p.admission_record(task, "decl")
    assert p.answer_for(task, query) == p.survivor_answer(True)
    assert p.encoded(task) == before_bytes
    assert p.answer_for(task, query) == p.survivor_answer(True)
    task["records"].append({"id": "b", "payload": "b"})
    task["quotient"]["b"] = "payload"
    task["demands"] = [["a", "ab"], ["ab", "b"], ["blank", "a"]]
    query["admission"] = p.admission_record(task, "decl")
    result = p.answer_for(task, query)
    assert result["before"] == [["a", "ab"], ["ab", "b"]]
    assert result["current"] == [["ab", "b"]] and result["delta"] == 1
    assert {tuple(x) for x in result["current"]} < {tuple(x) for x in result["before"]}
    task["demands"] = []
    query["admission"] = p.admission_record(task, "decl")
    result = p.answer_for(task, query)
    assert result["current"] == [] and result["delta"] == 0


@pytest.mark.parametrize("field,value", [
    ("receipt_id", True), ("receipt_id", "Invalid"), ("decision", "PROPOSE"), ("scope", "GLOBAL"),
    ("task_sha256", "0" * 64), ("candidate_sha256", "0" * 64)])
def test_bad_admission_fields(field, value):
    task = p.example_task()
    receipt = p.admission_record(task, "decl")
    receipt[field] = value
    with pytest.raises(p.InvalidInput):
        p.answer_for(task, {"kind": "survivors", "candidate_id": "decl", "admission": receipt})


def test_admission_stale_task_candidate_and_missing_witness():
    for surface in ("task_id", "quotient", "demands", "selector", "observer", "cost", "alphabet"):
        task = p.example_task()
        receipt = p.admission_record(task, "decl")
        if surface == "task_id":
            task["task_id"] = "other"
        elif surface == "quotient":
            task["quotient"]["a"] = "empty"
        elif surface == "demands":
            task["demands"] = []
        else:
            field = {"selector": "selector", "observer": "observer", "cost": "cost", "alphabet": "output_alphabet"}[surface]
            task["candidates"][0][field] = {"selector": [], "observer": "literal", "cost": 2, "alphabet": p.ALPHABET + ">"}[surface]
        with pytest.raises(p.InvalidInput):
            p.answer_for(task, {"kind": "survivors", "candidate_id": "decl", "admission": receipt})
    task = p.example_task()
    for receipt in ({}, [], True, {**p.admission_record(task, "decl"), "approved": True}):
        with pytest.raises(p.InvalidInput):
            p.answer_for(task, {"kind": "survivors", "candidate_id": "decl", "admission": receipt})
    with pytest.raises(p.InvalidInput):
        p.answer_for(task, {"kind": "survivors", "candidate_id": "del", "admission": p.admission_record(task, "decl")})


def test_all_small_cost_vectors_and_eligibility():
    checked = 0
    task = p.example_task()
    for flags in itertools.product((False, True), repeat=4):
        for costs in itertools.product(range(3), repeat=4):
            checked += 1
            task["candidates"] = [{"id": f"c{i}", "operation": "decl", "selector": ["a"] if flags[i] else [],
                                  "output_alphabet": p.ALPHABET, "observer": "selected", "cost": costs[i]} for i in range(4)]
            expected = [i for i in range(4) if flags[i]]
            minimum = min((costs[i] for i in expected), default=None)
            result = p.answer_for(task, {"kind": "costs"})
            assert result == {"scope": "DECLARED_FAMILY_AND_COSTS", "eligible": [f"c{i}" for i in expected],
                              "minimum_cost": minimum, "minimum_ids": [f"c{i}" for i in expected if costs[i] == minimum],
                              "equivalence": "SAME_PARTITION_ON_ORIGINAL_DOMAIN",
                              "partition_classes": [[f"c{i}" for i in expected]] if expected else []}
    assert checked == 1296


def test_invalid_cheapest_ties_partition_equivalence_and_unique_forcing():
    task = p.example_task()
    task["candidates"][2]["cost"] = task["candidates"][3]["cost"] = 0
    expected = p.answer_for(task, {"kind": "costs"})
    assert expected["minimum_ids"] == ["decl", "del"] and expected["minimum_cost"] == 1
    assert expected["partition_classes"] == [["decl", "del"]]
    for permutation in itertools.permutations(task["candidates"]):
        assert p.answer_for({**task, "candidates": list(permutation)}, {"kind": "costs"}) == expected
    task["candidates"][0]["cost"] = 0
    assert p.answer_for(task, {"kind": "costs"})["minimum_ids"] == ["decl"]
    assert p.answer_for(task, {"kind": "unique"}) == {"refusal": "ref<2>", "reason": "NO_UNCONDITIONAL_SELECTION"}
    task["records"].append({"id": "b", "payload": "b"})
    task["quotient"]["b"] = "payload"
    task["candidates"][1]["observer"] = "selected"
    task["candidates"][1]["selector"] = ["ab"]
    assert p.answer_for(task, {"kind": "costs"})["partition_classes"] == [["decl"], ["del"]]
    task["candidates"] = []
    assert p.answer_for(task, {"kind": "costs"})["minimum_cost"] is None
    assert p.answer_for(task, {"kind": "family"}) == {"candidate_ids": [], "count": 0, "classification": "SUPPLIED_NOT_EXHAUSTIVE"}


@pytest.mark.parametrize("mutate", [
    lambda t: t.update(extra=1), lambda t: t.pop("downstream"), lambda t: t.update(task_id=True),
    lambda t: t.update(records=[]), lambda t: t["records"].append(deepcopy(t["records"][0])),
    lambda t: t["records"][0].update(id="Bad"), lambda t: t["records"][0].update(payload=True),
    lambda t: t["records"][0].update(payload="a"*33), lambda t: t["records"][0].update(payload=">"),
    lambda t: t["records"][0].update(extra=0), lambda t: t.update(quotient={}),
    lambda t: t["quotient"].update(a=True), lambda t: t.update(downstream={"a":"0","ab":"1","blank":"0"}),
    lambda t: t["downstream"].pop("empty"), lambda t: t["downstream"].update(extra="0"),
    lambda t: t["downstream"].update(empty=True), lambda t: t["downstream"].update(empty="x"*65),
    lambda t: t.update(demands=True), lambda t: t.update(demands=[["a"]]),
    lambda t: t.update(demands=[["a","missing"]]), lambda t: t.update(demands=[[True,"a"]]),
    lambda t: t.update(demands=[["a","a"]]), lambda t: t.update(demands=[["a","ab"],["ab","a"]]),
    lambda t: t.update(candidates=None), lambda t: t["candidates"].append(deepcopy(t["candidates"][0])),
    lambda t: t["candidates"][0].update(id=[]), lambda t: t["candidates"][0].update(operation="invent"),
    lambda t: t["candidates"][0].update(selector=True), lambda t: t["candidates"][0].update(selector=["a","a"]),
    lambda t: t["candidates"][0].update(selector=["missing"]), lambda t: t["candidates"][0].update(selector=[{}]),
    lambda t: t["candidates"][0].update(output_alphabet=""), lambda t: t["candidates"][0].update(output_alphabet="aa"),
    lambda t: t["candidates"][0].update(output_alphabet=True), lambda t: t["candidates"][0].update(output_alphabet="\n"),
    lambda t: t["candidates"][0].update(observer="invent"), lambda t: t["candidates"][0].update(cost=True),
    lambda t: t["candidates"][0].update(cost=1.0), lambda t: t["candidates"][0].update(cost=-1),
    lambda t: t["candidates"][0].update(cost=1000001),
])
def test_invalid_task_contracts(mutate):
    task = p.example_task()
    mutate(task)
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


def test_collection_bounds():
    for field, size in (("records",17),("demands",65),("candidates",17)):
        task = p.example_task()
        task[field] = [{}] * size
        with pytest.raises(p.InvalidInput):
            p.validate_task(task)
    task = p.example_task()
    task["candidates"][0]["selector"] = ["a"] * 17
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


@pytest.mark.parametrize("query", [
    None, [], {}, {"kind":[]}, {"kind":"invent"}, {"kind":"family","extra":1},
    {"kind":"collision","left":True,"right":"ab"}, {"kind":"collision","left":"missing","right":"ab"},
    {"kind":"factor","values":{"a":"0"}}, {"kind":"factor","values":{"a":True,"ab":"0","blank":"0"}},
    {"kind":"refinement","new_quotient":{},"forget":{}}, {"kind":"effect","candidate_id":"missing"},
    {"kind":"effect","candidate_id":True}, {"kind":"survivors","candidate_id":"decl"}])
def test_invalid_query_shapes(query):
    with pytest.raises(p.InvalidInput):
        p.answer_for(p.example_task(), query)


def test_proposal_binding_boolean_types_and_snapshot():
    task = p.example_task()
    query = {"kind":"collision","left":"a","right":"ab"}
    answer = {"left_class":"payload","right_class":"payload","collision":True}
    document = p.submission(task, query, answer)
    result = p.evaluate(document)
    stable = p.encoded(result)
    assert result["verdict"] == "MATCH"
    answer["collision"] = 1
    assert p.evaluate(document)["verdict"] == "MISMATCH"
    result["original"]["task"]["demands"].clear()
    assert task["demands"] == [["a","ab"]]
    result = p.evaluate(p.submission(task, query, {**answer,"collision":True}))
    assert p.encoded(result) == stable
    task["task_id"] = "changed"
    with pytest.raises(p.InvalidInput):
        p.evaluate(document)
    assert p.encoded(result) == stable
    document = p.submission(p.example_task(), {"kind":"authority"}, {})
    document["proposal"]["problem_sha256"] = "0"*64
    with pytest.raises(p.InvalidInput):
        p.evaluate(document)


@pytest.mark.parametrize("mutate", [lambda d:d.update(extra=1),lambda d:d["proposal"].update(extra=1),
                                     lambda d:d["proposal"].update(answer=[]),lambda d:d["proposal"].update(answer={"large":"x"*p.MAX_BYTES})])
def test_invalid_proposal_shapes(mutate):
    document = p.submission(p.example_task(), {"kind":"authority"}, {})
    mutate(document)
    with pytest.raises(p.InvalidInput):
        p.evaluate(document)


@pytest.mark.parametrize("value", ["\ud800","\udfff"], ids=("high","low"))
def test_surrogate_rejection_retains_raw_input(value, tmp_path, capsys):
    task = p.example_task()
    task["downstream"]["empty"] = value
    with pytest.raises(p.InvalidInput, match="UTF-8"):
        p.validate_task(task)
    raw = b" \n" + p.encoded(p.submission(task, {"kind":"baseline"}, {})) + b"\t"
    source = tmp_path/"in.json"
    source.write_bytes(raw)
    assert p.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")]) == 1
    message = json.loads(capsys.readouterr().out)
    assert message["status"] == "REJECTED"
    assert (Path(message["output"])/"input.bin").read_bytes() == raw


@pytest.mark.parametrize("raw", [b"",b"{",b"\xff",b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b" "*(p.MAX_BYTES+1)],
                         ids=("empty","malformed","utf8","duplicate","nan","infinity","oversize"))
def test_bad_raw_bytes(raw, tmp_path, capsys):
    source = tmp_path/"input.json"
    source.write_bytes(raw)
    output = tmp_path/"runs"
    assert p.main(["--input",str(source),"--output-dir",str(output)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not output.exists()


def test_decode_requires_bytes_and_unicode_values():
    for value in (None,"",bytearray(b"{}")):
        with pytest.raises(p.InvalidInput):
            p.decode(value)
    task = p.example_task()
    task["downstream"]["payload"] = "\U0001f600"
    assert p.answer_for(task, {"kind":"recovery","left":"a","right":"ab"})["outputs"] == ["\U0001f600"]*2


def test_raw_receipt_hashes_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(p,"uuid4",lambda:SimpleNamespace(hex="fixed"))
    raw = b' \n {"original":1}\t'
    folder = p.write_run(tmp_path, {"ok":True}, raw, "MATCH")
    assert (folder/"input.bin").read_bytes() == raw
    receipt = json.loads((folder/"receipt.json").read_bytes())
    assert set(receipt["artifact_sha256"]) == {"input.bin","result.json","summary.md"}
    assert receipt["code_sha256"] == hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    for name, expected in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == expected
    with pytest.raises(FileExistsError):
        p.write_run(tmp_path, {"new":True}, b"new", "MATCH")
    assert (folder/"input.bin").read_bytes() == raw


@pytest.mark.parametrize("kind,status", [("match","MATCH"),("wrong","MISMATCH"),("invalid","REJECTED"),("default","DEMONSTRATED")])
def test_actual_cli(kind, status, tmp_path):
    command = [sys.executable,str(RUNNER),"--output-dir",str(tmp_path/"runs")]
    raw = None
    if kind != "default":
        task = p.example_task()
        document = {} if kind == "invalid" else p.submission(task,{"kind":"authority"},
                      {"refusal":"ref<2>","reason":"NO_ACTION_AUTHORITY"} if kind == "match" else {})
        raw = b" \n"+p.encoded(document)+b"\t"
        source = tmp_path/"input.json"
        source.write_bytes(raw)
        command += ["--input",str(source)]
    result = subprocess.run(command,text=True,capture_output=True,timeout=20,check=False)
    assert result.returncode == (1 if kind in ("wrong","invalid") else 0), result.stderr
    message = json.loads(result.stdout)
    assert message["status"] == status
    folder = Path(message["output"])
    assert json.loads((folder/"receipt.json").read_bytes())["status"] == status
    if raw is not None:
        assert (folder/"input.bin").read_bytes() == raw
    if kind == "default":
        assert json.loads((folder/"result.json").read_bytes()) == p.exercise_report()


def test_main_branches(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert p.main([]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"
    source = tmp_path/"input.json"
    source.write_bytes(p.encoded(p.submission(p.example_task(),{"kind":"authority"},{})))
    assert p.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "MISMATCH"
    source.write_bytes(b"{}")
    assert p.main(["--input",str(source),"--output-dir",str(tmp_path/"runs")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    assert p.main(["--input",str(tmp_path/"missing")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    source.write_bytes(b"blocking directory")
    assert p.main(["--output-dir",str(source)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"


MUTATIONS = (
    ("record_identity_for_quotient", "equal = left == right", 'equal = query["left"] == query["right"]', "test_all_small_partitions"),
    ("ignore_factor_conflict", "label in factor and factor[label] != value", "False", "test_all_small_partitions"),
    ("ignore_bad_projection", "forget[new[name]] != old[name]", "False", "test_all_small_refinement"),
    ("forget_old_information", '(task["quotient"][name], observations[name])', '("ignored", observations[name])', "test_deletion_separation"),
    ("overmatch_selector", "if name in selected:", 'if "a" in payload:', "test_four_operations"),
    ("insertion_erases", 'output = payload + "a"', 'output = ""', "test_nonseparating"),
    ("ignore_output_grammar", "if invalid:", "if False:", "test_nonseparating"),
    ("opaque_becomes_literal", 'observations[name] = "payload" if value else "empty"', "observations[name] = value", "test_nonseparating"),
    ("prediction_is_adoption", "current = after if has_admission else before", "current = after", "test_survivors_proposed"),
    ("erase_all_survivors", 'return sorted([list(sorted(pair)) for pair in demands if quotient[pair[0]] == quotient[pair[1]]])', "return []", "test_all_small_demand"),
    ("repeat_demands_allowed", "canonical not in demands", "True", "test_invalid_task_contracts"),
    ("unbound_admission_task", 'receipt["task_sha256"] == digest(task)', "True", "test_bad_admission_fields"),
    ("unbound_admission_candidate", 'receipt["candidate_sha256"] == digest(candidate)', "True", "test_bad_admission_fields"),
    ("ineffective_is_eligible", 'result["status"] != "CHECKED" or result["survivors"]', 'result["status"] != "CHECKED"', "test_all_small_cost"),
    ("drop_tied_minima", '[candidate["id"] for candidate in eligible if candidate["cost"] == minimum]', '[candidate["id"] for candidate in eligible if candidate["cost"] == minimum][:1]', "test_all_small_cost"),
    ("boolean_cost_allowed", 'type(candidate["cost"]) is int', 'isinstance(candidate["cost"], int)', "test_invalid_task_contracts"),
    ("unbound_proposal", 'document["proposal"]["problem_sha256"] == problem', "True", "test_proposal_binding"),
    ("no_snapshot", "snapshot = decode(raw)", "snapshot = document", "test_proposal_binding"),
    ("boolean_number_equal", 'encoded(snapshot["proposal"]["answer"]) == encoded(computed)', 'snapshot["proposal"]["answer"] == computed', "test_proposal_binding"),
    ("raw_bytes_stripped", '"input.bin": raw_input', '"input.bin": raw_input.strip()', "test_raw_receipt"),
    ("overwrite_allowed", "exist_ok=False", "exist_ok=True", "test_raw_receipt"),
    ("duplicate_keys_allowed", 'require(key not in result, "Duplicate JSON key")', 'require(True, "Duplicate JSON key")', "test_bad_raw"),
    ("utf8_guard_removed", 'value.encode("utf-8")', "None", "test_surrogate_rejection"),
)


def test_implementation_mutations(tmp_path):
    original = RUNNER.read_bytes()
    source = RUNNER.read_text(encoding="utf-8")
    rows = []
    for name, anchor, replacement, selected in MUTATIONS:
        assert source.count(anchor) == 1, (name,source.count(anchor))
        mutant_text = source.replace(anchor,replacement)
        compile(mutant_text,name,"exec")
        mutant = tmp_path/(name+".py")
        mutant.write_text(mutant_text,encoding="utf-8")
        environment = dict(os.environ,PFP_PILOT_000012_UNDER_TEST=str(mutant),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                           PYTHONDONTWRITEBYTECODE="1",NO_COLOR="1")
        for variable in ("PFP_PILOT_000012_MUTATION_OUTPUT","FORCE_COLOR","PY_COLORS"):
            environment.pop(variable,None)
        result = subprocess.run([sys.executable,"-m","pytest",str(Path(__file__)),"-q","--color=no","-p","no:cacheprovider","-o","addopts=",
                                 "--import-mode=importlib","--basetemp",str(tmp_path/(name+"_temp")),"-k",selected],
                                env=environment,text=True,capture_output=True,timeout=40,check=False)
        failures = [line for line in result.stdout.splitlines() if line.startswith("FAILED ")]
        assert result.returncode == 1 and failures, (name,result.returncode,result.stdout,result.stderr)
        assert RUNNER.read_bytes() == original
        rows.append({"name":name,"anchor":anchor,"replacement":replacement,"target":str(RUNNER.resolve()),
                     "applied":True,"exit_code":result.returncode,"failed_nodes":failures,"original_unchanged":True,
                     "original_sha256":hashlib.sha256(original).hexdigest(),"mutant_sha256":hashlib.sha256(mutant.read_bytes()).hexdigest()})
    if output := os.environ.get("PFP_PILOT_000012_MUTATION_OUTPUT"):
        with Path(output).open("x",encoding="utf-8") as stream:
            json.dump(rows,stream,indent=2)


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(RUNNER), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert p.OUTPUT_ROOT == RUNNER.resolve().parent.parent / "pilot_output" / p.PILOT_ID


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    computed = p.answer_for

    def drifted(task, query):
        answer = computed(task, query)
        return {**answer, "count": 99} if query["kind"] == "baseline" else answer

    monkeypatch.setattr(p, "answer_for", drifted)
    report = p.exercise_report()
    assert [row["id"] for row in report["exercises"] if row["result"]["verdict"] == "MISMATCH"] == ["DRILL2.5"]
    assert p.demonstration_status(report) == "MISMATCH"
    assert p.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
