"""Replay the retained G12 proof, gate, mutation and custody evidence."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("_paper011_g12", PAPER / "code/genesis_g12_replay.py")
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)


@pytest.fixture(scope="module")
def receipt() -> dict:
    return json.loads((replay.AREA / "receipt.json").read_bytes())


def test_fixed_blob_sources_and_sealed_iso(receipt):
    manifest = replay.verify_sources()
    assert len(manifest["files"]) == 86
    assert receipt["source_manifest_sha256"] == replay.MANIFEST_SHA
    assert receipt["source_pin"] == replay.PIN
    assert receipt["sealed_iso_pin"] == replay.SEALED
    raw = (replay.PACKAGE / "original/lean4/Derivation/Minimality.lean").read_bytes()
    sealed = (replay.AREA / "sealed_Minimality.lean").read_bytes()
    def block(data):
        return b"structure Iso" + data.split(b"structure Iso", 1)[1].split(b"def isoRefl", 1)[0]
    assert block(raw) == block(sealed)
    assert replay.sha(block(raw)) == receipt["sealed_iso_declaration_sha256"]


def test_actual_environment_census_and_both_held_out_definitions(receipt):
    census = replay.read_json_output("final_census", "G12_CENSUS=")
    dump = replay.read_json_output("final_independentdump", "G12_INDEPENDENT_DUMP=")
    selected = replay.check_independent(census, dump)
    assert len(dump) == 12 and sum(len(m["constNames"]) for m in dump) == 141
    assert len(selected) == len(receipt["reports"]) == 5
    assert {n for _, n in selected} >= {"Derivation.Iso.trans", "Derivation.Iso.symm"}
    assert {r["definition"] for r in receipt["reports"]} == {n for _, n in selected}


@pytest.mark.parametrize("mutation", ["drop_symm", "duplicate", "missing_constant"])
def test_census_corruptions_cannot_pass(mutation):
    census = replay.read_json_output("final_census", "G12_CENSUS=")
    dump = replay.read_json_output("final_independentdump", "G12_INDEPENDENT_DUMP=")
    if mutation == "drop_symm":
        census = [r for r in census if r["definition"] != "Derivation.Iso.symm"]
    elif mutation == "duplicate":
        census.append(copy.deepcopy(census[0]))
    else:
        dump[0]["constants"].pop()
    with pytest.raises(ValueError):
        replay.check_independent(census, dump)


def test_manifest_substitution_and_response_corruption_are_refused(tmp_path, monkeypatch):
    (tmp_path / "source_manifest.json").write_text('{"source_commit":"replacement"}', encoding="utf8")
    monkeypatch.setattr(replay, "AREA", tmp_path)
    with pytest.raises(ValueError, match="SOURCE_MANIFEST_CHANGED"):
        replay.verify_sources()
    raw = (PAPER / "docs/history_recovery/g12/final_census_stdout.txt").read_bytes()
    record = json.loads((PAPER / "docs/history_recovery/g12/final_census_process.json").read_bytes())
    (tmp_path / "test_stdout.txt").write_bytes(raw + b"corruption")
    (tmp_path / "test_process.json").write_bytes(replay.wire(record))
    with pytest.raises(ValueError, match="UNBOUND_OR_FAILED_PROCESS"):
        replay.read_json_output("test", "G12_CENSUS=")
    record["returncode"] = 1
    (tmp_path / "test_stdout.txt").write_bytes(raw)
    (tmp_path / "test_process.json").write_bytes(replay.wire(record))
    with pytest.raises(ValueError, match="UNBOUND_OR_FAILED_PROCESS"):
        replay.read_json_output("test", "G12_CENSUS=")


def test_exact_prop_pins_and_real_axiom_reports(receipt):
    actual = replay.read_json_output("final_audit", "G12_REPORTS=")
    assert actual == receipt["reports"]
    assert len({r["instance"] for r in actual}) == 5
    for report in actual:
        assert report["status"] == "SOLVED"
        assert set(report["axioms"]) <= {"propext", "Quot.sound"}
        assert set(report["instance_axioms"]) <= {"propext", "Quot.sound"}
    assert all(p["returncode"] == 0 for p in receipt["processes"])
    assert any("FrozenPins.lean" in " ".join(p["argv"]) for p in receipt["processes"])


def test_valid_but_altered_and_vacuous_statements_are_actually_rejected(receipt):
    controls = {m["mutation"]: m for m in receipt["mutations"]}
    for name, expected in (("false_hypothesis", "VACUOUS_WRAPPER"),
                           ("dropped_hypothesis", "STATEMENT_PIN_MISMATCH")):
        row = controls[name]
        assert row["reason"] == expected and row["process"]["returncode"] != 0
        assert expected in (PAPER / row["process"]["stdout_path"]).read_text(encoding="utf8")


def test_text_census_and_misplaced_theorem_compile_but_are_refused(receipt):
    controls = {m["mutation"]: m for m in receipt["mutations"]}
    assert controls["text_matched_census"]["process"]["returncode"] == 0
    with pytest.raises(ValueError, match="CENSUS_NOT_ENVIRONMENT_DERIVED"):
        replay.require_census_custody(controls["text_matched_census"]["process"])
    assert controls["wrapper_in_ParkedAudit"]["process"]["returncode"] == 0
    with pytest.raises(ValueError, match="WRAPPER_IN_AUDIT_APPARATUS"):
        replay.require_candidate_location(replay.PACKAGE / "controls/ParkedAudit.lean")
    with pytest.raises(ValueError, match="WRAPPER_IN_AUDIT_APPARATUS"):
        replay.require_candidate_location(replay.PACKAGE / "original/lean4/Derivation/Probe.lean")


def test_original_lexical_policy_detects_comment_poison(receipt):
    control = next(m for m in receipt["mutations"] if m["mutation"] == "sorry_in_instance_comment")
    assert control["compile_process"]["returncode"] == 0
    assert control["gate_process"]["returncode"] != 0
    output = (PAPER / control["gate_process"]["stdout_path"]).read_text(encoding="utf8")
    assert "forbidden token 'sorry'" in output
    assert "only " not in output


def test_original_48_reports_and_full_axiom_artifact_gates_preserved(receipt):
    artifact = (replay.PACKAGE / "original/artifacts/lean_axioms.txt").read_text(encoding="utf8")
    assert sum(line.startswith("ParkedAudit.lean:") for line in artifact.splitlines()) == 48
    assert len(receipt["original_gates"]) == 3
    assert all(gate["returncode"] == 0 for gate in receipt["original_gates"])
    assert not receipt["entire_external_run_gates_executed"]


def test_process_streams_and_direct_inputs_are_bound(receipt):
    processes = [*receipt["processes"], *receipt["original_gates"]]
    for mutation in receipt["mutations"]:
        processes.extend(v for key, v in mutation.items() if key.endswith("process"))
    for process in processes:
        assert process["direct_inputs_before"] == process["direct_inputs_after"]
        for stream in ("stdout", "stderr"):
            assert replay.sha((PAPER / process[stream + "_path"]).read_bytes()) == process[stream + "_sha256"]
        assert process["argv"] and Path(process["cwd"]).is_dir()


def test_runtime_inputs_stay_immutable_and_do_not_claim_os_or_models(receipt):
    snapshots = []
    for phase in ("before", "after"):
        raw = (replay.AREA / ("runtime_inputs_" + phase + ".json")).read_bytes()
        assert replay.sha(raw) == receipt["runtime_inputs_" + phase + "_sha256"]
        snapshots.append(json.loads(raw))
    before, after = snapshots
    assert all(after[path] == value for path, value in before.items())
    assert all(str(PAPER / row["recovered_path"]) in before for row in replay.verify_sources()["files"])
    assert before[str(PAPER / "code/genesis_g12_replay.py")]["sha256"] == replay.sha((PAPER / "code/genesis_g12_replay.py").read_bytes())
    assert receipt["dont_write_bytecode"] and not any(Path(receipt["cache_prefix"]).iterdir())
    assert "outside" in receipt["runtime_scope"]
    assert receipt["model_arms_executed"] == []
    assert not receipt["empirical_differentiation_gate"]
    assert not receipt["full_G12_experiment_completed"]
    assert receipt["AuthorityEffect"] == "None"
