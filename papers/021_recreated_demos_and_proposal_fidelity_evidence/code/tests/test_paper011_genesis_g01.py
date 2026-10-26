"""Discriminating original G01 mathematics, refusal and custody regressions."""
import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("paper011_genesis_g01_test_adapter", CODE / "genesis_g01_replay.py")
g01 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g01)


@pytest.fixture(scope="module")
def original():
    return g01.load_original()


def test_sealed_definition_bytes_and_original_pins():
    manifest = g01.verify_sources()
    core = [row for row in manifest["files"] if row["source_path"].startswith("lean4/Derivation/")
            and row["commit"] == g01.SEALED]
    assert len(core) == 3
    assert all(row["git_blob"] == row["b55_identical_blob"] for row in core)
    assert next(row["git_blob"] for row in core if row["source_path"].endswith("Basic.lean")) == "610d8fc982853807eb892eaaf683fc4eb2959cc1"


def test_genesis_mark_refused_but_target_marks_remain_valid(original):
    c, engine, model = (original[name] for name in ("candidates", "engine", "model"))
    base = model.replay(engine.READING_F.genesis)
    for datum in range(3):
        delta = (c.NewForm(1), c.NewInst(0, (datum,)))
        assert c.response_valid_naive(base, (1, 2), delta) is (datum != 0)


@pytest.mark.parametrize("reading,measure,count,classes,cost", [
    ("F", "mu1", 10, 5, [2, -1]), ("F", "mu2", 2, 1, [2, 1]),
    ("L", "mu1", 6, 3, [2, -1]), ("L", "mu2", 2, 1, [2, 1]),
])
def test_original_minima_and_unpruned_crosscheck(original, reading, measure, count, classes, cost):
    result = g01.python_finite(original, reading, measure)
    assert len(result["deltas"]) == count
    assert len(result["classes"]) == classes
    assert result["cost"] == cost
    assert all(row["size"] == 2 for row in result["classes"])


def test_five_shapes_do_not_collapse_under_genesis_relabelling(original):
    c, engine, iso, model = (original[name] for name in ("candidates", "engine", "iso", "model"))
    base = model.replay(engine.READING_F.genesis)
    renamed = iso.rename(base, (1, 0, 2), ())
    result = c.min_responses(renamed, (0, 2), "mu1", c.Bounds(2, 2))
    keys = {iso.canonical(model.replay((model.Impose(0, 2),) + c.delta_events(renamed, delta), renamed))
            for delta in result.deltas}
    assert len(result.deltas) == 10
    assert len(keys) == 5


@pytest.mark.parametrize("source,hit", [
    ("-- sorry in a comment", "sorry"), ("-- unsafe", "unsafe"),
    ("axiom fictitious : True", "axiom-line"),
    ("partial def loop : Nat := loop", "partial"),
    ("import Mathlib", "outside-core-import"),
])
def test_original_lexical_gate_also_scans_comments(source, hit):
    assert hit in g01.token_violations(source)


def test_valid_minimum_source_does_not_trigger_lexical_guard():
    source = (g01.PACKAGE / "ResearchG01.lean").read_text(encoding="utf8")
    assert g01.token_violations(source) == []


@pytest.fixture(scope="module")
def native():
    build = json.loads((g01.AREA / "native_build_v3/receipt.json").read_bytes())
    assert build["returncode"] == 0
    executable = Path(build["executable"])
    assert g01.sha(executable.read_bytes()) == build["executable_sha256"]
    return executable


@pytest.mark.parametrize("request_bytes,error", [
    (b"{", "MALFORMED_JSON"),
    (g01.wire({"reading": "F", "measure": "mu1", "max_items": 2, "max_arity": 3}), "OUTSIDE_ORIGINAL_BOUNDS"),
    (g01.wire({"reading": "other", "measure": "mu1", "max_items": 2, "max_arity": 2}), "UNDECLARED_READING"),
    (g01.wire({"reading": "F", "measure": "other", "max_items": 2, "max_arity": 2}), "UNDECLARED_MEASURE"),
    (g01.wire({"reading": "F", "measure": "mu1", "max_items": 2, "max_arity": 2, "drop_genesis": True}), "REQUEST_FIELDS"),
])
def test_native_cannot_extend_bounds_or_change_reading(native, request_bytes, error):
    result = subprocess.run([str(native)], input=request_bytes, capture_output=True, timeout=30)
    assert result.returncode == 2
    assert json.loads(result.stdout) == {"status": "REFUSED", "error": error}


def test_actual_native_retains_all_ten_deltas_and_five_classes(native):
    request = g01.wire({"reading": "F", "measure": "mu1", "max_items": 2, "max_arity": 2})
    result = subprocess.run([str(native)], input=request, capture_output=True, timeout=30)
    assert result.returncode == 0
    value = json.loads(result.stdout)
    assert value["status"] == "COMPUTED"
    assert len(value["deltas"]) == 10
    assert len(value["classes"]) == 5
    assert sum(row["size"] for row in value["classes"]) == 10


def test_refined_label_difference_does_not_replace_membership_verification(native, original):
    python = g01.python_finite(original, "F", "mu1")
    result = subprocess.run([str(native)], input=g01.wire(python["request"]), capture_output=True, timeout=30)
    assert result.returncode == 0
    value = json.loads(result.stdout)
    assert value["deltas"] != json.loads(g01.wire(python["deltas"]))
    assert g01.normalize_finite(value) == g01.normalize_finite(python)
    corrupt = copy.deepcopy(value)
    corrupt["classes"][0]["size"] += 1
    with pytest.raises(ValueError, match="CLASS_MEMBERSHIP_OR_SIZE_DISAGREEMENT"):
        g01.normalize_finite(corrupt)
    corrupt = copy.deepcopy(value)
    corrupt["classes"].pop()
    with pytest.raises(ValueError, match="CLASS_QUOTIENT_NOT_COMPLETE"):
        g01.normalize_finite(corrupt)


def test_closed_theorem_gate_preserves_poison_and_empirical_boundaries():
    receipt = json.loads((g01.AREA / "theorem_run_v3/receipt.json").read_bytes())
    assert receipt["clean_build"] and receipt["all_axioms_within_whitelist"]
    assert receipt["target_pins"] == 11
    assert receipt["mutations_rejected"] == 7
    assert receipt["valid_control_accepted"]
    assert [row["outcome"] for row in receipt["heldouts"]] == ["SOLVED"] * 5 + ["OUT_OF_SCOPE"] * 3
    assert not receipt["model_accuracy_gate"] and not receipt["owner_pr_gate"]
    assert not receipt["estate_twelve_family_gate"] and not receipt["F5_plus_Lean_exact_class_gate"]
    assert receipt["runtime_before_sha256"] == receipt["runtime_after_sha256"]


def test_native_decide_classical_and_false_mutations_hit_distinct_real_gates():
    rows = json.loads((g01.AREA / "theorem_run_v3/mutations.json").read_bytes())
    compiled = {row["id"]: row for row in rows if row["compile_attempted"]}
    assert compiled["M02_native_decide"]["expected_gate_error"] == "DISALLOWED_AXIOM candidate._native.native_decide.ax_1_1"
    assert compiled["M03_classical_em"]["expected_gate_error"] == "DISALLOWED_AXIOM Classical.choice"
    assert compiled["M05_false_hypothesis"]["expected_gate_error"] == "STATEMENT_PIN_MISMATCH"
    assert all(not compiled[name]["accepted"] for name in ("M02_native_decide", "M03_classical_em", "M05_false_hypothesis"))
    assert compiled["VALID_CONTROL"]["accepted"]


def test_corrupted_success_bytes_cannot_become_a_judge_result(monkeypatch, tmp_path):
    stream = tmp_path / "stdout.bin"
    stream.write_bytes(b'G01_PINS=[{"matched":true}]\n')
    record = {"returncode": 0, "stdout_path": "stdout.bin", "stdout_sha256": g01.sha(stream.read_bytes())}
    monkeypatch.setattr(g01, "PAPER", tmp_path)
    stream.write_bytes(b'G01_PINS=[{"matched":false}]\n')
    with pytest.raises(ValueError, match="FAILED_OR_UNBOUND_JUDGE_OUTPUT"):
        g01.output_marker(record, "G01_PINS=")
