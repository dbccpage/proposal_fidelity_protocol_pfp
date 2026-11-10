"""Independent finite oracles, mutation controls, and custody checks; never provider evidence."""
import copy
import json
from fractions import Fraction as Q
from itertools import product

import pytest
import yaml
from sympy import Matrix

from omega_engine_pfp.infrastructure.model_loading import load_yaml_model

from . import run
from .cases import IDS, PILOTS, canonical, carrier, sha, surface
from .checking import check_answer, evaluate
from .prepare import CAMPAIGN, ROOT, historical_bytes, historical_plan
from .run import grade, load_case, microusd, reservation


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
    return historical_plan()


@pytest.mark.parametrize("pilot", ["pilot_0000000", "pilot_0000188"])
def test_capsule_reader_uses_declared_current_owner(tmp_path, monkeypatch, pilot):
    education = tmp_path / "education"
    pfp = tmp_path / "omega_engine_pfp" / "tests"
    owner = pfp if pilot == "pilot_0000000" else education
    folder = owner / pilot / "tests" / "test_00"
    folder.mkdir(parents=True)
    raw = b"value: unchanged\n"
    (folder / "input.yaml").write_bytes(raw)
    monkeypatch.setattr(run, "ROOT", tmp_path)
    monkeypatch.setattr(run, "PILOTS", education)
    row = dict(capsule=f"{pilot}/tests/test_00", input_sha256=sha(raw))
    found, case = run.load_case(row)
    assert found == folder and case == {"value": "unchanged"}
    assert row == dict(capsule=f"{pilot}/tests/test_00", input_sha256=sha(raw))


@pytest.mark.parametrize("fault", ["missing", "tampered"])
def test_capsule_reader_never_falls_back_from_canonical_owner(tmp_path, monkeypatch, fault):
    capsule = "pilot_0000000/tests/test_00"
    education = tmp_path / "education"
    old = education / capsule
    old.mkdir(parents=True)
    raw = b"value: original\n"
    (old / "input.yaml").write_bytes(raw)
    canonical = tmp_path / "omega_engine_pfp" / "tests" / capsule
    canonical.mkdir(parents=True)
    if fault == "tampered":
        (canonical / "input.yaml").write_bytes(b"value: tampered\n")
    monkeypatch.setattr(run, "ROOT", tmp_path)
    monkeypatch.setattr(run, "PILOTS", education)
    error = FileNotFoundError if fault == "missing" else ValueError
    with pytest.raises(error):
        run.load_case(dict(capsule=capsule, input_sha256=sha(raw)))


@pytest.mark.parametrize("capsule", ["../outside", "/absolute/path", "C:/absolute/path"])
def test_capsule_reader_rejects_escaped_or_absolute_identity(capsule):
    with pytest.raises(ValueError, match="INVALID_CAPSULE_PATH"):
        run.load_case(dict(capsule=capsule, input_sha256="0" * 64))


def test_current_environment_and_explicit_legacy_keys_preserve_true_drift():
    current = run.environment()
    assert run.environment_matches(current)
    archived = yaml.safe_load(historical_bytes("matrix/replay_custody_20261011/free_followup/authorization.yaml"))
    old_checker = "omega_engine_education/pfp/domain/pilots/checker_registry.py"
    # This is a new current-source fixture with old keys, not rewritten historical metadata.
    rebound = {path: sha(run._source_bytes(path)) for path in archived["environment"]["sources"]}
    assert run.source_bindings_match(rebound)
    rebound[old_checker] = archived["environment"]["sources"][old_checker]
    assert not run.source_bindings_match(rebound)
    prior_keys = tuple(run.LEGACY_SOURCE_ARCHIVE) + (run.ACTIVE_DEPENDENCIES[3],) + tuple(run.LEGACY_PROVIDER_SOURCES)
    prior = {path: sha(run._source_bytes(path)) for path in prior_keys}
    assert run.source_bindings_match(prior)
    prior[run.ACTIVE_DEPENDENCIES[3]] = "0" * 64
    assert not run.source_bindings_match(prior)
    assert not run.source_bindings_match({"unknown/source.py": "0" * 64})
    with pytest.raises(ValueError, match="UNREGISTERED_REPLAY_SOURCE"):
        run._source_bytes("unknown/source.py")


def test_retired_plan_is_read_only_and_missing_history_refuses(monkeypatch):
    from . import prepare as preparation
    assert len(preparation.prepare()["cases"]) == 250
    assert not (PILOTS / "matrix" / f"{CAMPAIGN}.yaml").exists()
    with pytest.raises(ValueError, match="UNREGISTERED_HISTORICAL"):
        historical_bytes("../outside.yaml")
    monkeypatch.setattr(preparation, "HISTORICAL_REVISION", "0" * 40)
    with pytest.raises(ValueError, match="HISTORICAL_CAMPAIGN_BYTES_UNAVAILABLE"):
        preparation.prepare()


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
    def preserved(target):
        prefix = "omega_engine_education/pilots/"
        if type(target) is not str or not target.startswith(prefix):
            raise ValueError("UNREGISTERED_PRESERVED_SOURCE")
        return ROOT / "omega_engine_woland/tests/pilots" / target[len(prefix):]

    manifest = json.loads(historical_bytes(f"matrix/migration_custody_20261011/{CAMPAIGN}_sources.json"))
    assert len(manifest["files"]) >= 30
    for row in manifest["files"]:
        assert sha(preserved(row["target"]).read_bytes()) == row["sha256"]
    custody_root = PILOTS / "matrix" / "replay_custody_20261011" / "free_followup"
    custody = json.loads(historical_bytes("matrix/replay_custody_20261011/free_followup/manifest.json"))
    authorization_path = custody_root / "authorization.yaml"
    assert custody["source_path"] == "omega_engine_education/pilots/matrix/dossier_replay_20261011/free_followup/authorization.yaml"
    authorization_bytes = historical_bytes("matrix/replay_custody_20261011/free_followup/authorization.yaml")
    assert not authorization_path.exists()
    assert sha(authorization_bytes) == custody["sha256"]
    authorization = yaml.safe_load(authorization_bytes)
    sources = authorization["environment"]["sources"]
    for path in run.LEGACY_SOURCE_ARCHIVE:
        assert sha(run._source_bytes(path)) == sources[path]
    # The current checker changed after this run. Historical custody survives,
    # but its old environment must not be promoted into a current replay PASS.
    checker = "omega_engine_education/pfp/domain/pilots/checker_registry.py"
    assert sha(run._source_bytes(checker)) != sources[checker]
    assert not run.source_bindings_match(sources)
    retired = json.loads((PILOTS / "pilot_0000188" / "misc" / "retired_dossier_trials_runner_v1" / "manifest.json").read_text())
    assert retired["status"] == "retained_exact_bytes_before_relocation"
    for row in retired["files"]:
        assert sha(preserved(row["preserved_path"]).read_bytes()) == row["sha256"]


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
    from omega_engine_pfp.infrastructure.taxonomy.task_families import VALID_TASK_FAMILIES

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


def test_retired_source_directories_have_current_custody():
    for directory in ("mode_trials", "dossier_trials", "migration"):
        assert not (PILOTS / directory).exists()
    assert not (PILOTS / "matrix" / "source_directory_retirement_20261011.yaml").exists()
    assert not (PILOTS / "matrix" / "migration_custody_20261011").exists()
    assert not (PILOTS / "matrix" / "replay_custody_20261011").exists()
    assert (PILOTS / "replay_runners" / "mode_capsules").is_dir()
    assert (PILOTS / "replay_runners" / "dossier_capsules").is_dir()


def test_guidance_preserves_carriers_and_has_no_answer_examples():
    followup = historical_plan("_guidance")
    parents = {row["capsule"]: row for row in plan()["cases"]}
    assert len(followup["cases"]) == 50
    for row in followup["cases"]:
        _, case = load_case(row)
        _, original = load_case(parents[row["parent_capsule"]])
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
    from omega_engine_pfp.domain.types import PilotSpec, SeedPrompt
    from omega_engine_pfp.domain.types.rewrite_test_plan import RewriteTestPlan
    folder = PILOTS / f"pilot_{pilot:07d}"
    for model, name in ((PilotSpec, "spec.yaml"), (SeedPrompt, "seed.yaml"), (RewriteTestPlan, "testplan.yaml")):
        load_yaml_model(model, folder / name)
