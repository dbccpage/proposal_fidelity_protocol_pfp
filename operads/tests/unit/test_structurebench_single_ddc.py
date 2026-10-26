"""New wire names preserve the existing structural constraint identities."""
import hashlib
import json
import pytest

from omega_engine_operads.structurebench.evaluator import ConstraintOutcome, StructureBenchEvaluator


def bundle(path):
    payloads = {"uns.md": b"# Universal Narrative\n", "ddc.jsonl": b'{"payload":{"letter":"C"}}\n',
                "uts.jsonl": b'{"kind":"run_checkpoint"}\n', "summary.json": b'{}\n'}
    receipt = {"bundle_schema_version": "omega.woland.reported-run-bundle.v2"}
    for name, raw in payloads.items():
        (path / name).write_bytes(raw)
        receipt[name.split('.')[0] + "_sha256"] = hashlib.sha256(raw).hexdigest()
    (path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return StructureBenchEvaluator(path)


def test_fresh_names_use_same_constraint_ids_without_duplicate_tape(tmp_path):
    evaluator = bundle(tmp_path)
    assert evaluator._c1_files_present().outcome is ConstraintOutcome.SATISFIED
    assert evaluator._c2_hash_binding().outcome is ConstraintOutcome.SATISFIED
    assert evaluator._read("novella.md") == (tmp_path / "uns.md").read_bytes()
    assert evaluator._read("dda_actions.jsonl") == (tmp_path / "ddc.jsonl").read_bytes()
    assert not list(tmp_path.glob("dda*"))


def test_fresh_missing_uts_and_changed_ddc_are_actual_structural_failures(tmp_path):
    evaluator = bundle(tmp_path)
    (tmp_path / "uts.jsonl").unlink()
    (tmp_path / "ddc.jsonl").write_bytes(b"counterfeit\n")
    assert evaluator._c1_files_present().outcome is ConstraintOutcome.VIOLATED
    assert evaluator._c2_hash_binding().outcome is ConstraintOutcome.VIOLATED


@pytest.mark.parametrize("tape_name", ["ddc.jsonl", "dda_actions.jsonl"])
def test_pre_uns_single_tape_layouts_keep_their_original_names(tmp_path, tape_name):
    files = {"novella.md": b"Retained pre-UNS narrative\n", tape_name: b'{"letter":"C"}\n',
             "summary.json": b'{}\n'}
    receipt = {}
    for name, raw in files.items():
        (tmp_path / name).write_bytes(raw)
        receipt[name.split('.')[0] + "_sha256"] = hashlib.sha256(raw).hexdigest()
    (tmp_path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    evaluator = StructureBenchEvaluator(tmp_path)
    assert evaluator._c1_files_present().outcome is ConstraintOutcome.SATISFIED
    assert evaluator._c2_hash_binding().outcome is ConstraintOutcome.SATISFIED
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
