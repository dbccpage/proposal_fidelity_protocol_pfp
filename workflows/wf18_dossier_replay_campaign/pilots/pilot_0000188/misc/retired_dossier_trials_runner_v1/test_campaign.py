"""Independent finite oracles, mutation controls, and custody checks; never provider evidence."""
import copy
from fractions import Fraction as Q
from itertools import product
import json

import pytest
from sympy import Matrix
import yaml

from .cases import IDS, PILOTS, canonical, carrier, sha, surface
from .checking import check_answer, evaluate
from .prepare import CAMPAIGN, ROOT
from .run import grade, load_case, microusd, reservation
from . import run


def reference(t):
    """Fixture constructor only. Production accepts witnesses by recomputation."""
    kind = t["kind"]
    if kind == "linear":
        x = Matrix(t["matrix"]).inv() * Matrix(t["b"])
        return dict(solution=[str(v) for v in x], target=str((Matrix([t["target"]])*x)[0]))
    if kind in ("graph", "repair"):
        import networkx as nx
        graph = nx.Graph()
        graph.add_nodes_from(range(t["n"]))
        graph.add_edges_from(t["edges"])
        if kind == "repair":
            forest = nx.minimum_spanning_tree(graph)
            return dict(removed=[i for i, e in enumerate(t["edges"]) if not forest.has_edge(*e)], cycle_rank=0)
        bridges = {frozenset(e) for e in nx.bridges(graph)}
        return dict(components=sorted(sorted(g) for g in nx.connected_components(graph)),
                    bridges=[i for i, e in enumerate(t["edges"]) if frozenset(e) in bridges],
                    cycle_rank=graph.number_of_edges()-graph.number_of_nodes()+nx.number_connected_components(graph),
                    triangles=sum(nx.triangles(graph).values())//3)
    if kind == "lookup":
        edge = next((e for e in t["edges"] if set(e[:2]) == set(t["query"])), None)
        return dict(code="MAP_UNDEFINED" if edge is None else "MISSING_LENGTH" if edge[2] is None else "VALUE",
                    value=None if edge is None else edge[2])
    if kind == "spin":
        candidates = []
        for bits in product([0, 1], repeat=t["n"]):
            r = [(t["target"][i]+bits[a]+bits[b]) % 2 for i, (a, b) in enumerate(t["edges"])]
            candidates.append(dict(spins=list(bits), residual=r, weight=sum(r)))
        return min(candidates, key=lambda a: a["weight"])
    if kind == "lp":
        a, g = Matrix(t["matrix"]), Matrix(t["flux"])
        cycle = a.T.nullspace()[0]
        pairing = (g.T*cycle)[0]
        weights = list(map(Q, t["weights"]))
        scale = min(Q(w)/abs(Q(v)) for w, v in zip(weights, cycle) if v)
        v = cycle * (scale if pairing >= 0 else -scale)
        # An optimum residual supported on the cheapest cycle coordinate.
        i = min((i for i, z in enumerate(cycle) if z), key=lambda i: weights[i]/abs(Q(cycle[i])))
        residual = Matrix.zeros(len(g), 1)
        residual[i] = pairing / cycle[i]
        x, params = a.gauss_jordan_solve(g-residual)
        x = x.subs({p: 0 for p in params})
        return dict(potential=[str(z) for z in x], dual=[str(z) for z in v], objective=str((g.T*v)[0]))
    if kind == "scope":
        matrices = list(map(Matrix, t["matrices"]))
        ranks = [a.rank() for a in matrices]
        dims = [matrices[0].cols] + [a.rows for a in matrices]
        ok = all(b*a == Matrix.zeros(b.rows, a.cols) for a, b in zip(matrices, matrices[1:]))
        betti = [dims[i]-([0]+ranks)[i]-(ranks+[0])[i] for i in range(5)] if ok else None
        return dict(ranks=ranks, betti=betti, topology_status="CHAIN_LAW_FAILURE" if not ok else "MATCH" if betti == t["declared_betti"] else "DECLARED_TOPOLOGY_MISMATCH", cup_status="UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER")
    raise AssertionError(kind)


def envelope(answer):
    return dict(derived_under_policy="SPK-001", answer=answer,
        summary=dict(narrowest_defensible_thesis="Finite fixture witness", evidence_scope="Declared carrier only", next_concrete_test="Check a changed carrier"),
        process_integrity=dict(seed_allows_theory_refutation=True, should_continue=False), sections=[])


@pytest.mark.parametrize("pilot,rung", product(IDS, range(1, 6)))
def test_independent_oracle_and_wrong_witness(pilot, rung):
    t = carrier(pilot, rung)
    answer = reference(t)
    assert check_answer(t, answer)
    bad = copy.deepcopy(answer)
    if t["kind"] == "linear":
        bad["solution"][0] = str(Q(bad["solution"][0])+1)
    elif t["kind"] == "graph":
        bad["cycle_rank"] += 1
    elif t["kind"] == "repair":
        bad["removed"] = []
    elif t["kind"] == "lookup":
        bad["code"] = "MAP_UNDEFINED" if bad["code"] != "MAP_UNDEFINED" else "MISSING_LENGTH"
    elif t["kind"] == "spin":
        bad["weight"] += 1
    elif t["kind"] == "lp":
        bad["objective"] = str(Q(bad["objective"])+1)
    else:
        bad["ranks"][0] += 1
    assert not check_answer(t, bad)


def plan():
    return yaml.safe_load((PILOTS / "matrix" / f"{CAMPAIGN}.yaml").read_text())


@pytest.mark.parametrize("row", plan()["cases"], ids=lambda r: r["capsule"])
def test_every_wrapped_case_and_strict_ingress(row):
    _, case = load_case(row)
    task = case["task"]
    schema = yaml.safe_load(case["prompt"]["response_schema"])
    valid = envelope(reference(task))
    assert evaluate(task, json.dumps(valid), schema)["status"] == "HOST_ACCEPTED"
    assert evaluate(task, json.dumps(valid["answer"]), schema)["status"] == "TYPED_REFUSAL"
    valid["unlicensed"] = True
    assert evaluate(task, json.dumps(valid), schema)["status"] == "TYPED_REFUSAL"
    assert evaluate(task, '{"answer":0,"answer":1}', schema)["status"] == "TYPED_REFUSAL"
    text, legend = surface(task, case["representation"])
    recovered = json.loads("".join(legend[t] for t in text.split())) if legend else json.loads(text)
    assert recovered == task and sha(canonical(task)) == case["carrier_sha256"]
    public = case["prompt"]["system_prompt"] + case["prompt"]["user_prompt"]
    assert "SPK-001" in public and "Response schema:" in public
    assert "expected_answer" not in public and "[PROMPT ID]" not in public


def test_numeric_coercion_and_alternative_witnesses():
    task = carrier(188, 4)
    answer = reference(task)
    alternative = dict(answer, spins=[1-s for s in answer["spins"]])
    assert check_answer(task, alternative)
    answer["spins"][0] = bool(answer["spins"][0])
    with pytest.raises(Exception):
        check_answer(task, answer)
    task = carrier(189, 3)
    answer = reference(task)
    answer["potential"] = [str(Q(v)+7) for v in answer["potential"]]
    assert check_answer(task, answer)
    answer["objective"] = float(Q(answer["objective"]))
    with pytest.raises(Exception):
        check_answer(task, answer)


def test_preserved_source_bytes():
    manifest = json.loads((PILOTS / "migration" / f"{CAMPAIGN}_sources.json").read_text())
    assert len(manifest["files"]) >= 30
    for row in manifest["files"]:
        assert sha((ROOT / row["target"]).read_bytes()) == row["sha256"]


def test_budget_and_unknown_billing():
    for value in (None, True, "NaN", -1):
        with pytest.raises(ValueError):
            microusd(value)
    _, case = load_case(plan()["cases"][0])
    assert reservation(case, {"row": {"pricing": {"prompt": "0", "completion": "0"}}}) == 0
    result = dict(id="fixture-only", model="fixture", choices=[{"message": {"content": "{}"}}],
                  usage=dict(prompt_tokens=1, completion_tokens=1, total_tokens=2))
    with pytest.raises(ValueError, match="UNRECONCILED_COST"):
        grade(case, canonical(result), "fixture")


@pytest.mark.parametrize("mutation", ["input", "request", "reply", "receipt", "model", "checker"])
def test_replay_tampering_refuses(tmp_path, monkeypatch, mutation):
    _, case = load_case(plan()["cases"][0])
    capsule = tmp_path / "pilot" / "tests" / "test_00"
    capsule.mkdir(parents=True)
    input_bytes = yaml.safe_dump(case).encode()
    (capsule / "input.yaml").write_bytes(input_bytes)
    row = dict(capsule="pilot/tests/test_00", input_sha256=sha(input_bytes))
    config = dict(model="fixture", environment=run.environment())
    reply = canonical(dict(id="fixture-only", model="fixture",
        choices=[dict(message=dict(content=json.dumps(envelope(reference(case["task"])))), finish_reason="stop")],
        usage=dict(prompt_tokens=1, completion_tokens=1, total_tokens=2, cost=0)))
    wire = canonical(run.request_wire(case, "fixture"))
    receipt = dict(**grade(case, reply, "fixture"), environment=config["environment"],
        input_sha256=sha(input_bytes), request_sha256=sha(wire), provider_response_sha256=sha(reply))
    (capsule / "provider_response.json").write_bytes(reply)
    (capsule / "request.json").write_bytes(wire)
    (capsule / "response.yaml").write_text(yaml.safe_dump(receipt))
    monkeypatch.setattr(run, "PILOTS", tmp_path)
    assert run.replay_one(row, config)["status"] == "HOST_ACCEPTED"
    if mutation in ("input", "request", "reply"):
        path = capsule / {"input": "input.yaml", "request": "request.json", "reply": "provider_response.json"}[mutation]
        path.write_bytes(path.read_bytes()+b" ")
    elif mutation == "receipt":
        receipt["code"] = "MADE_UP_PASS"
        (capsule / "response.yaml").write_text(yaml.safe_dump(receipt))
    elif mutation == "model":
        config["model"] = "different"
    else:
        monkeypatch.setattr(run, "environment", lambda: {"changed": True})
    with pytest.raises(ValueError):
        run.replay_one(row, config)


def test_campaign_taxonomy_and_counts():
    from omega_engine_education.pfp.infrastructure.taxonomy.task_families import VALID_TASK_FAMILIES
    from .cases import FAMILIES
    assert set(FAMILIES.values()) <= VALID_TASK_FAMILIES
    rows = plan()["cases"]
    assert len(rows) == 250 and len(set(r["capsule"] for r in rows)) == 250
    assert all(sum(r["pilot_id"] == f"pilot_{p:07d}" for r in rows) == 25 for p in IDS)


def test_retired_demo_and_complete_chain_carrier():
    assert not (PILOTS / "demo_003").exists()
    from .cases import source_input
    source = source_input(190)
    matrices = [Matrix(source["boundary_matrices"][f"d{i}"]) for i in range(4)]
    assert all(b*a == Matrix.zeros(b.rows, a.cols) for a, b in zip(matrices, matrices[1:]))


def test_guidance_preserves_carriers_and_has_no_answer_examples():
    path = PILOTS / "matrix" / f"{CAMPAIGN}_guidance.yaml"
    followup = yaml.safe_load(path.read_text())
    assert len(followup["cases"]) == 50
    for row in followup["cases"]:
        _, case = load_case(row)
        original = yaml.safe_load((PILOTS / row["parent_capsule"] / "input.yaml").read_text(encoding="utf-8"))
        for key in ("task", "representation", "rung", "carrier_sha256"):
            assert case[key] == original[key]
        assert case["prompt"]["response_schema"] == original["prompt"]["response_schema"]
        assert case["prompt"]["user_prompt"].startswith(original["prompt"]["user_prompt"])


@pytest.mark.parametrize("pilot", [188, 189, 190, 191])
def test_original_dossier_certificate_survives_migration(pilot):
    from .cases import source_input
    t = source_input(pilot)
    w = json.loads((PILOTS / f"pilot_{pilot:07d}" / "misc/source/witness_valid.json").read_text(encoding="utf-8"))
    if pilot == 188:
        task = dict(kind="spin", n=3, edges=[[0, 1], [1, 2], [2, 0]], target=t["target_cochain"]["values"])
        c = w["candidate_solution"]
        answer = dict(spins=c["spin_vector"], residual=c["residual_defect"], weight=c["defect_weight"])
    elif pilot == 189:
        task = dict(kind="lp", matrix=t["matrices"]["d0"], flux=t["target_cochain"]["values"], weights=[e["weight"] for e in t["carrier"]["edges"]])
        answer = dict(potential=w["primal_candidate"]["alpha"], dual=w["dual_witness"]["w"], objective=w["primal_candidate"]["primal_objective"])
    elif pilot == 190:
        task = dict(kind="lp", matrix=t["boundary_matrices"]["d3"], flux=[p["flux_g"] for p in t["topology"]["pentachora"]], weights=[p["weight"] for p in t["topology"]["pentachora"]])
        answer = dict(potential=w["potential_c"], dual=w["dual_witness"], objective=w["reported_value"])
    else:
        c = w["instanton_certificate"]
        task = dict(kind="lp", matrix=t["boundary_matrices"]["d3"], flux=c["pontryagin_4cochain"], weights=["1"])
        answer = dict(potential=c["potential_c"], dual=c["dual_witness"], objective=c["reported_value"])
        scope = carrier(191, 1)
        verdict = reference(scope)
        assert verdict["topology_status"] == "DECLARED_TOPOLOGY_MISMATCH"
        assert check_answer(scope, verdict)
    assert check_answer(task, answer)


@pytest.mark.parametrize("pilot", [188, 189, 190, 191])
def test_standard_pilot_documents(pilot):
    from omega_engine_education.pfp.domain import PilotSpec, SeedPrompt
    from omega_engine_education.pfp.domain.types.rewrite_test_plan import RewriteTestPlan
    folder = PILOTS / f"pilot_{pilot:07d}"
    for model, name in ((PilotSpec, "spec.yaml"), (SeedPrompt, "seed.yaml"), (RewriteTestPlan, "testplan.yaml")):
        model.from_yaml(folder / name)
