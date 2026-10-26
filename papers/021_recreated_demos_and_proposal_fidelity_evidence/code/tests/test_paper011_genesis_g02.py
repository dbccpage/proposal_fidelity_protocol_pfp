"""Independent target, census, mutation, and byte-custody checks for original G02."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("_paper011_g02", PAPER / "code/genesis_g02_replay.py")
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)


@pytest.fixture(scope="module")
def run():
    folder = replay.AREA / "final_v3"
    receipt = json.loads((folder / "receipt.json").read_bytes())
    return folder, receipt


def test_literal_original_definition_slice_and_git_objects():
    manifest = replay.verify_sources()
    assert manifest["source_commit"] == "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
    source = (replay.AREA / "original/lean4/Derivation/HigherStructure.lean").read_text(encoding="utf8")
    blocks = []
    for start, end in (("def subsetsOf", "/-- The *cut census*"),
                       ("def cutCensus", "/-- On two occurrences")):
        first = source.index(start)
        blocks.append(source[first:source.index(end, first)].rstrip())
    expected = "import Lean\n\nnamespace HigherStructure\n\n" + "\n\n".join(blocks) + "\n\nend HigherStructure\n"
    assert (replay.PACKAGE / "CutDefinitions.lean").read_text(encoding="utf8") == expected
    for row in manifest["files"]:
        raw = (PAPER / row["recovered_path"]).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == row["git_blob"]


def test_actual_original_general_target_pins_and_heldouts(run):
    folder, receipt = run
    pins = (replay.PACKAGE / "Pins.lean").read_text(encoding="utf8")
    assert "∀ n, 2 ≤ n → cutCensus n 0 1 = 2 ^ (n - 2) := C2" in pins
    assert "∀ n a b, a < n → b < n → a ≠ b → cutCensus n a b = 2 ^ (n - 2) := C3" in pins
    assert "cutCensus 9 0 1 = 128 := C3_at_nine" in pins
    assert "cutCensus 10 0 1 = 256 := C3_at_ten" in pins
    assert "cutCensus 9 3 1 = 128 := relabel_pair" in pins
    process = json.loads((folder / "clean_lake_build_process.json").read_bytes())
    assert process["returncode"] == 0
    stdout = (folder / "clean_lake_build_stdout.bin").read_bytes()
    assert replay.sha(stdout) == process["stdout_sha256"]
    assert b"Built Pins" in stdout
    reports = json.loads((folder / "actual_axiom_reports.json").read_bytes())
    assert replay.check_reports(reports) == receipt["target_statuses"]
    assert len([r for r in reports if r["public_target"]]) == 13
    assert all(set(r["axioms"]) <= {"propext", "Quot.sound"} for r in reports)
    for target in ("C1", "C2", "C3"):
        assert receipt["target_statuses"][target]["lean_names"] == [f"ResearchPaper011G02.{target}"]


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "extra_axiom", "renamed"])
def test_report_corruption_cannot_pass(run, corruption):
    reports = json.loads((run[0] / "actual_axiom_reports.json").read_bytes())
    reports = copy.deepcopy(reports)
    chosen = next(r for r in reports if r["name"] == "ResearchPaper011G02.C3")
    if corruption == "missing":
        reports.remove(chosen)
    elif corruption == "duplicate":
        reports.append(copy.deepcopy(chosen))
    elif corruption == "extra_axiom":
        chosen["axioms"].append("Classical.choice")
    else:
        chosen["name"] = "EasierTask.C3"
    with pytest.raises(ValueError):
        replay.check_reports(reports)


def test_every_pair_through_twelve_matches_independent_formula(run):
    folder, receipt = run
    rows = json.loads((folder / "census_rows.json").read_bytes())
    expected = {(n, a, b) for n in range(13) for a in range(n + 2) for b in range(n + 2)}
    assert len(rows) == receipt["enumerated_pair_cases"] == len(expected) == 1014
    assert {(r["n"], r["a"], r["b"]) for r in rows} == expected
    for row in rows:
        n, a, b = row["n"], row["a"], row["b"]
        count = 0 if a >= n or a == b else 2 ** (n - (1 if b >= n else 2))
        assert row["source_sublist_count"] == count
        assert row["native_count"] == str(count)
        assert row["subsets_enumerated_per_route"] == 2 ** n
    public = {(r["n"], r["a"], r["b"]): r["source_sublist_count"] for r in rows}
    assert [public[(n, 0, 1)] for n in (5, 6, 7, 8)] == [8, 16, 32, 64]
    assert public[(0, 0, 1)] == 0 and public[(3, 0, 0)] == 0


def test_native_response_is_directly_bound_to_the_full_request_and_replays(run):
    folder, receipt = run
    request = (folder / "native_request.json").read_bytes()
    process = json.loads((folder / "bitmask_census_process.json").read_bytes())
    assert process["stdin_sha256"] == replay.sha(request)
    assert process["stdin_bytes"] == len(request)
    assert process["returncode"] == 0
    executable = Path(process["argv"][0])
    before = replay.sha(executable.read_bytes())
    native = subprocess.run([str(executable)], input=request, capture_output=True, check=True, timeout=30)
    assert native.stdout == (folder / "bitmask_census_stdout.bin").read_bytes()
    assert before == replay.sha(executable.read_bytes())
    results = json.loads(native.stdout)["cases"]
    assert len(results) == receipt["enumerated_pair_cases"] + 2
    assert [(r["case_id"], r["success"], r["error"]) for r in results[-2:]] == [
        ("TOO_LARGE", False, "CARRIER_LIMIT_12"), ("FLOAT_CARRIER", False, "NATURAL_N_REQUIRED")]


def test_all_original_mutants_rejected_and_known_valid_candidate_preserved(run):
    folder, receipt = run
    rows = json.loads((folder / "mutation_results.json").read_bytes())
    expected = {"native_decide": "FORBIDDEN_NATIVE_DECIDE", "sorry_docstring": "FORBIDDEN_SORRY",
                "open_classical": "FORBIDDEN_OPEN_CLASSICAL", "unverified_nat_pow": "DISALLOWED_REPLACEMENT_AXIOM",
                "narrowed_pin": "STATEMENT_PIN_MISMATCH", "valid_control": None}
    assert len(rows) == 6 and rows == receipt["mutations"]
    assert {r["mutation"]: r["reason"] for r in rows} == expected
    for row in rows:
        source = (folder / row["candidate_path"]).read_bytes()
        assert replay.sha(source) == row["candidate_sha256"]
        assert row["compile_returncode"] == 0
        assert row["outcome"] == ("ACCEPTED" if row["mutation"] == "valid_control" else "REJECTED")
        if row["mutation"] in {"sorry_docstring", "open_classical"}:
            assert not row["disallowed_axioms"]
            assert replay.lexical_refusal(source) == row["reason"]
        if row["mutation"] == "native_decide":
            assert row["disallowed_axioms"]
        if row["mutation"] == "narrowed_pin":
            assert row["pin_returncode"] != 0 and not row["disallowed_axioms"]
            raw = (folder / "mutation_narrowed_pin_pin_stdout.bin").read_bytes()
            assert b"Type mismatch" in raw


def test_process_and_source_custody_and_experiment_limits(run):
    folder, receipt = run
    for name, digest in receipt["outputs"].items():
        assert replay.sha((folder / name).read_bytes()) == digest
    before = json.loads((folder / "inputs_before.json").read_bytes())
    after = json.loads((folder / "inputs_after.json").read_bytes())
    assert before == after
    for path in (replay.PACKAGE / "cut_bitmask.rs", replay.PACKAGE / "lake-manifest.json",
                 replay.PACKAGE / "CutDefinitions.lean", PAPER / "code/genesis_g02_replay.py"):
        assert before[str(path)] == replay.sha(path.read_bytes())
    build = json.loads((replay.AREA / "native_build_v1/receipt.json").read_bytes())
    assert build["libraries_before"] == build["libraries_after"]
    assert build["source_sha256"] == replay.sha((replay.PACKAGE / "cut_bitmask.rs").read_bytes())
    assert receipt["mutation_suite_complete"] is True
    assert receipt["model_arms_executed"] is False
    assert receipt["entire_external_estate_workflow_executed"] is False
    assert receipt["full_G02_experiment_completed"] is False


def test_supplement_binds_each_actual_generated_compiler_input(run):
    folder = replay.AREA / "mutation_custody_v1"
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["baseline_receipt_sha256"] == replay.sha((run[0] / "receipt.json").read_bytes())
    assert receipt["baseline_helper_sha256"] == replay.sha((PAPER / "code/genesis_g02_replay.py").read_bytes())
    assert receipt["mutations"] == run[1]["mutations"]
    assert len(receipt["processes"]) == 8
    for name, digest in receipt["outputs"].items():
        assert replay.sha((folder / name).read_bytes()) == digest
    before = json.loads((folder / "inputs_before.json").read_bytes())
    assert before == json.loads((folder / "inputs_after.json").read_bytes())
    for process in receipt["processes"]:
        inputs = process["compiler_inputs_before"]
        assert inputs == process["compiler_inputs_after"] and len(inputs) == 1
        for path, digest in inputs.items():
            assert replay.sha(Path(path).read_bytes()) == digest
            assert path == process["argv"][1]
        assert replay.sha((folder / f'{process["name"]}_stdout.bin').read_bytes()) == process["stdout_sha256"]
        assert replay.sha((folder / f'{process["name"]}_stderr.bin').read_bytes()) == process["stderr_sha256"]


def test_substituted_source_manifest_is_refused(tmp_path, monkeypatch):
    (tmp_path / "source_manifest.json").write_bytes(b'{"source_commit":"easier-task"}')
    monkeypatch.setattr(replay, "AREA", tmp_path)
    with pytest.raises(ValueError, match="ORIGINAL_MANIFEST_CHANGED"):
        replay.verify_sources()
